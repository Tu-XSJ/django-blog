**简单的数据库设计**

***用户表(user)***
- user_id (UUID) 用户ID
- username (VARCHAR(150)) 用户名 

***文章表(article)***
- id 文章ID  自增主键
- title (VARCHAR(150)) 文章标题
- content (TEXT) 文章内容
- view_count (BIGINT) 文章总阅读次数
- uv_count (BIGINT) 用户人次
- update_at (DATETIME)

***记录表(read_records)***
- id 记录ID
- article 外键->articles.id 
- user 外键->user.id
- read_count (INT DEFAULT 0) 用户阅读次数

在 (article_id, user_id) 上建立联合唯一索引:UniqueConstraint(article, user)


**数据安全**

***读写分离***
- redis读
  - 设置热点key
  - 防止缓存击穿：当key过期的时候只允许一个请求访问数据库，在读库后顺便写入缓存
- redis写
  - 需要先检查key是否存在：不存在的话需要先从数据库恢复

***异步写回数据库***
- 配置redis的aof：每秒 刷盘（或者使用两台redis）
- celery异步把数据持久化到mysql

**分层**

***使用service层处理复杂的redis逻辑***
- redis的pipeline保证原子性
- 先查缓存，没查到查数据库，然后写入缓存

***views***
- 调用service
- 返回数据