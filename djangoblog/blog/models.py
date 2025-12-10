from django.db import models
from django.db import transaction

import uuid
# Create your models here.

class User(models.Model):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150,db_index=True)

class Article(models.Model):
    title = models.CharField(max_length=150)
    content = models.TextField()
    view_count = models.BigIntegerField(default=0,help_text="文章总阅读次数")
    uv_count = models.BigIntegerField(default=0,help_text="用户人次")
    updated_at = models.DateTimeField(auto_now=True)
    def update_safely(self,total_views,total_uv):
        """
        防止title或者content被覆盖
        """
        self.view_count = total_views
        self.uv_count = total_uv
        self.save(update_fields=['view_count','uv_count','updated_at'])

class ReadRecord(models.Model):
    #多对一（多阅读记录对应一篇文章），文章被删除，阅读记录也要被删除,通过article反向查找readRecord
    article = models.ForeignKey(Article, on_delete=models.CASCADE,related_name='read_record')
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='read_record')
    read_count = models.BigIntegerField(default=0)

    class Meta:
        # 唯一索引
        constraints = [
            models.UniqueConstraint(fields=['article', 'user'], name='article_user_unique')
        ]


class ReadRecordManager(models.Manager):
    def from_redis(self,article,user_views):
        """
        将Redis中的用户阅读明细同步到数据库
        :param article: Article对象
        :param user_views:字典{user_id_str:content}
        """
        user_ids = list(user_views.keys())
        exit_records = self.filter(article=article,user_id_str__in=user_ids)
        exit_user_ids = set(str(r.user_id) for r in exit_records)

        #分成需要更新和创建的
        update=[]
        create=[]

        #更新
        for record in exit_records:
            user_id = str(record.user_id)
            count = user_views.get(user_id)

            if count and count > record.read_count:
                record.read_count = count
                update.append(record)

        #新建
        for user_id,count1 in user_views.items():
            if user_id not in exit_user_ids:
                create.append(self.model(
                    article=article,
                    user_id=user_id,
                    read_count=count1,
                ))

        # 批量执行SQL
        with transaction.atomic():
            if create:
                self.bulk_create(create,batch_size=1000)
            if update:
                self.bulk_update(update,['read_count'],batch_size=1000)
        return len(create),len(update)


