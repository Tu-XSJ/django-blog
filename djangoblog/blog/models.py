from django.db import models

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