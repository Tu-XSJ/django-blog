from django.db import models, transaction
from uuid import UUID
import uuid


class User(models.Model):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, db_index=True)


class Article(models.Model):
    title = models.CharField(max_length=150)
    content = models.TextField()
    view_count = models.BigIntegerField(default=0)
    uv_count = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def update_safely(self, total_views, total_uv):
        self.view_count = total_views
        self.uv_count = total_uv
        self.save(update_fields=['view_count', 'uv_count', 'updated_at'])


class ReadRecordManager(models.Manager):
    def from_redis(self, article, user_views):
        """
        user_views: { "uuid-string": int }
        """
        # 转成 UUID
        user_ids = [UUID(uid) for uid in user_views.keys()]
        

        # 查询已存在的记录
        exit_records = self.filter(article=article, user__in=user_ids)
        exit_user_ids = set(r.user_id for r in exit_records)

        update = []
        create = []

        # 需要更新
        for record in exit_records:
            uid = record.user_id
            count = user_views.get(str(uid))
            if count and count > record.read_count:
                record.read_count = count
                update.append(record)

        # 需要创建
        for uid_str, count1 in user_views.items():
            uid = UUID(uid_str)
            if uid not in exit_user_ids:
                create.append(self.model(
                    article=article,
                    user_id=uid,
                    read_count=count1,
                ))

        with transaction.atomic():
            if create:
                self.bulk_create(create, batch_size=1000)
            if update:
                self.bulk_update(update, ['read_count'], batch_size=1000)

        return len(create), len(update)


class ReadRecord(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='read_records'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='read_records'
    )
    read_count = models.BigIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['article', 'user'], name='article_user_unique')
        ]

    objects = ReadRecordManager()
