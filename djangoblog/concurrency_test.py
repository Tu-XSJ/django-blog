import os
import django
import threading
import time

# 初始化 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')
django.setup()

from django_redis import get_redis_connection
from blog.models import Article
from blog.services import ReadAndSaveService

# 1. 准备数据
redis = get_redis_connection("default")
article = Article.objects.create(title="Concurrency Test", view_count=999)
service = ReadAndSaveService(article.id)

# 清除缓存，制造“击穿”现场
redis.delete(service._key_view_count())
redis.delete(f"lock:article:{article.id}")

print(f"--- 开始测试文章 ID: {article.id} ---")
print("Redis缓存已清空，准备启动多线程...")

# 计数器：记录真正查库的次数
db_query_count = 0

# 这是一个作弊的方法：我们在 Service 的查库代码里加个打印，或者在这里通过 hack 方式统计
# 为了演示，我们修改一下 service 里的 _reload_from_db_with_lock 方法，
# 让它在查库时 print 一句话。
# (你需要在运行此脚本前，去 services.py 的 _reload_from_db_with_lock 里加一句 print)

def simulate_request(thread_id):
    # 模拟每个请求都去获取数据
    # 如果锁生效，50个线程应该瞬间完成，且数据库只被查1次
    views = service.get_stats()
    return views

threads = []
start_time = time.time()

# 启动 50 个线程同时请求
for i in range(50):
    t = threading.Thread(target=simulate_request, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

end_time = time.time()

print(f"--- 测试结束 ---")
print(f"耗时: {end_time - start_time:.4f}秒")
print("请检查你的控制台输出：")
print("如果你只看到【1次】 'Thread Safe DB Query'，说明锁成功了。")
print("如果你看到很多次，说明锁失败了。")