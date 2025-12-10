# blog/admin.py
from django.contrib import admin
from .models import Article, User, ReadRecord

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'view_count', 'uv_count')
    readonly_fields = ('view_count', 'uv_count') # 防止手贱修改

admin.site.register(User)
admin.site.register(ReadRecord)