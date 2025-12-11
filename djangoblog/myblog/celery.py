import os
from celery import Celery

#1、设置默认的Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')

#2、创建Celery实例
app = Celery('myblog')

#3、从Django settings加载配置
app.config_from_object('django.conf:settings', namespace='CELERY')

#4、自动发现每个app目录下的tasks.py文件
app.autodiscover_tasks()