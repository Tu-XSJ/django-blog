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
***记录表(read_records)***
- id 记录ID
- article 外键->articles.id 
- user 外键->user.id
- read_count (INT DEFAULT 0) 用户阅读次数
在 (article_id, user_id) 上建立联合唯一索引:UniqueConstraint(article, user)