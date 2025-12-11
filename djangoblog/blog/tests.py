from django.test import TestCase
from django_redis import get_redis_connection
from .models import Article,ReadRecord,User
from .services import ReadAndSaveService
import time

class ReadAndSaveServiceTest(TestCase):
    def setUp(self):
        # 1. 准备数据
        self.article = Article.objects.create(title="Test Article", content="Content")
        self.user_id = "user_001"
        self.service = ReadAndSaveService(self.article.id)
        self.redis = get_redis_connection("default")

        # 2. 【修改这里】使用 delete 来清理脏数据
        self.redis.delete(self.service._key_view_count())
        self.redis.delete(self.service._key_user_stats())
        self.redis.delete(self.service._key_dirty_set())

    def tearDown(self):
        # 【检查一下这里】如果有同样的问题，也要把 set 改成 delete
        self.redis.delete(self.service._key_view_count())
        self.redis.delete(self.service._key_user_stats())
        self.redis.delete(self.service._key_dirty_set())

    def test_record_view_logic(self):
        """测试：记录阅读量是否只写入redis"""
        #1、执行记录操作
        self.service.record_view(self.user_id)

        # 2. 验证 Redis 数据
        redis_views = self.redis.get(self.service._key_view_count())
        self.assertEqual(int(redis_views), 1)

        # 3. 验证 MySQL 数据 (此时应该还没动)
        self.article.refresh_from_db()
        self.assertEqual(self.article.view_count, 0)

        # 4. 验证脏数据集合
        is_dirty = self.redis.sismember("article:dirty_ids", self.article.id)
        self.assertTrue(is_dirty)

    def test_sync_data_to_db(self):
        """测试：同步数据从 Redis 到 MySQL"""

        # 1. 创建真实用户
        userA = User.objects.create(username="A")
        userB = User.objects.create(username="B")

        # 2. 使用真实 UUID 执行记录
        self.service.record_view(str(userA.user_id))
        self.service.record_view(str(userA.user_id))
        self.service.record_view(str(userB.user_id))

        # 3. 执行同步
        success = self.service.sync_data_to_db()
        self.assertTrue(success)

        # 4. 验证 Article（总数）
        self.article.refresh_from_db()
        self.assertEqual(self.article.view_count, 3)  # 总共3次
        self.assertEqual(self.article.uv_count, 2)  # A、B 两个人

        # 5. 验证 ReadRecord（明细）
        record_a = ReadRecord.objects.get(article=self.article, user=userA)
        self.assertEqual(record_a.read_count, 2)

        record_b = ReadRecord.objects.get(article=self.article, user=userB)
        self.assertEqual(record_b.read_count, 1)

    def test_cache_miss_and_reload(self):
        """测试：缓存失效后，能否从数据库正确回填"""
        # 1. 数据库里预设值为 100
        self.article.view_count = 100
        self.article.save()

        # 2. 确保 Redis 里没数据 (模拟缓存过期)
        self.redis.delete(self.service._key_view_count())

        # 3. 调用 get_stats (触发回源逻辑)
        views = self.service.get_stats()

        # 4. 验证返回值
        self.assertEqual(views, 100)

        # 5. 验证 Redis 是否被回填了
        cached_views = self.redis.get(self.service._key_view_count())
        self.assertEqual(int(cached_views), 100)
