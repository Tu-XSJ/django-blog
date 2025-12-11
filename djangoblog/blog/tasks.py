from celery import shared_task
from django_redis import get_redis_connection
from .services import ReadAndSaveService
import logging

logger = logging.getLogger(__name__)

@shared_task
def sync_data_task():
    """
        从redis的'dirty_ids'集合中取出所有变脏的文章ID，然后调用service同步到mysql
    """
    redis = get_redis_connection("default")

    count = 0

    while True:
        #每次取一个article_id
        articles_id = redis.spop("article:dirty_ids")

        if articles_id is None:
            break

        articles_id1 = articles_id.decode("utf-8")

        try:
            service = ReadAndSaveService(articles_id1)
            service.sync_data_to_db()
            count += 1
        except Exception as e:
            logger.error(e)
    return f"{count}文章放入DB"