import logging
import random
import time
from django.core.cache import cache
from django_redis import get_redis_connection
from .models import Article,ReadRecord


logger = logging.getLogger(__name__)

class ReadAndSaveService:
    def __init__(self,article_id):
        self.article_id = str(article_id)
        self.redis = get_redis_connection()

    #规范redis中key的定义
    def _key_view_count(self):
        return f"article:{self.article_id}:view_count"

    def _key_user_stats(self):
        return f"article:{self.article_id}:user_stats"

    # Set结构，记录哪些文章变脏了
    # 给celery看的“任务队列”,避免遍历全部文章
    def _key_dirty_set(self):
        return "article:dirty_ids"

    #写数据
    def record_view(self,user_id):
        try:
            #使用pipeline保证原子性
            pipe = self.redis.pipeline()

            pipe.incr(self._key_view_count())

            pipe.hincrby(self._key_user_stats(),user_id,1)

            pipe.sadd(self._key_dirty_set(),self.article_id)

            pipe.execute()
        except Exception as e:
            logger.error(f"redis出错了：{e}")

    #读数据
    def get_stats(self):
        """
        先查缓存，没查到,加锁，查数据库，并写入缓存
        """
        view_count = self.redis.get(self._key_view_count())

        if view_count is not None:
            return int(view_count)

        return self._reload_from_db_with_lock()

    def _reload_from_db_with_lock(self):

        lock_key = self.article_id
        #获取一个分布式锁对象
        #blocking_timeout=3 如果3秒抢不到锁就不抢了，直接放弃或者返回旧数据
        with self.redis.lock(lock_key,timeout=5,blocking_timeout=3):
            #第2重检查，可以在等等待锁的时候，就有人填数据了
            view_count = self.redis.get(self._key_view_count())
            if view_count is not None:
                return int(view_count)

        try:
            #从数据库加载数据
            article = Article.objects.get(pk=self.article_id)
            db_views = article.view_count
            expire_time = 8640+random.randint(0,3600)
            #写入redis
            self.redis.set(self._key_view_count(),db_views,ex=expire_time)

            return db_views
        except Article.DoesNotExist:
            #防止缓存穿透
            self.redis.set(self._key_view_count(),0,ex=60)
            return 0
        except Exception as e:
            self.redis.set(self._key_view_count(),0,ex=60)
            return 0

        #3、同步逻辑(给Celery任务调用)
    def sync_data_to_db(self):
        """
        将redis的数据落地到mysql
        """
        views = self.redis.get(self._key_view_count())
        user_stats = self.redis.hgetall(self._key_user_stats())

        if not views:
            return "没有数据"
        try:
            article = Article.objects.get(pk=self.article_id)

            #格式化用户数据
            formatted_user_stats = {
                k.decode('utf-8'):int(v)
                for k,v in user_stats.items()
            }

            #更新总数
            article.update_safely(
                total_views=int(views),
                total_uv=len(formatted_user_stats)
            )

            #更新明细表
            ReadRecord.objects.from_redis(
                article=article,
                user_views=formatted_user_stats
            )

            return True

        except Article.DoesNotExist:
            logger.error(f"Article {self.article_id} 找不到")
            return False

