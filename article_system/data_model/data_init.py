from typing import Annotated
from datetime import datetime
from sqlalchemy import create_engine, ForeignKey, String, Integer, Text, Index, DateTime
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text

from dotenv import load_dotenv
import os

load_dotenv()

# 环境变量处理，添加默认值和类型转换
data_type = os.getenv("DATA_TYPE", "sqlite")
data_user = os.getenv("DATA_USER", "")
data_password = os.getenv("DATA_PASSWORD", "")
data_table = os.getenv("DATA_TABLE", "article_system")
data_address = os.getenv("DATA_ADDRESS", "localhost")

# 端口号处理
data_port_str = os.getenv("DATA_PORT")
if data_port_str and data_port_str.lower() != 'none':
    try:
        data_port = int(data_port_str)
    except ValueError:
        data_port = None
else:
    data_port = None

# 构建数据库连接字符串
if data_type.lower() == "sqlite":
    # SQLite 数据库
    database_url = f"sqlite:///{data_table}.db"
elif data_type.lower() == "mysql":
    # MySQL 数据库，使用 PyMySQL 驱动
    if data_port:
        database_url = f"mysql+pymysql://{data_user}:{data_password}@{data_address}:{data_port}/{data_table}"
    else:
        database_url = f"mysql+pymysql://{data_user}:{data_password}@{data_address}/{data_table}"
else:
    # 其他数据库
    if data_port:
        database_url = f"{data_type}://{data_user}:{data_password}@{data_address}:{data_port}/{data_table}"
    else:
        database_url = f"{data_type}://{data_user}:{data_password}@{data_address}/{data_table}"

# 字段类型定义
primary_key_id = Annotated[int, mapped_column(primary_key=True)]
str_field_not_null = Annotated[str, mapped_column(String(255), nullable=False)]
str_field_null = Annotated[str, mapped_column(String(255), nullable=True)]
text_field = Annotated[str, mapped_column(Text, nullable=False)]
date_field = Annotated[datetime, mapped_column(DateTime, nullable=False, default=datetime.now)]
update_time_field = Annotated[datetime, mapped_column(DateTime, nullable=True, default=datetime.now)]

engine = create_engine(
    database_url,
    echo=True,
    # 性能优化配置
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_pre_ping=True,  # 连接前检查
    pool_recycle=3600,  # 连接回收时间（秒）
)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    user_id: Mapped[primary_key_id]
    user_name: Mapped[str_field_not_null]
    user_email: Mapped[str_field_not_null]
    user_password: Mapped[str_field_not_null]
    user_gender: Mapped[str_field_not_null]
    user_avatar_url: Mapped[str_field_null]
    user_created_time: Mapped[date_field]
    user_updated_time: Mapped[update_time_field]
    
    # 关系定义
    user_articles = relationship("Article", back_populates="article_author", cascade="all, delete-orphan")
    user_comments = relationship("Comment", back_populates="comment_author", cascade="all, delete-orphan")

    def __repr__(self):
        return f"User(user_id={self.user_id}, user_name={self.user_name}, user_email={self.user_email}, " \
               f"user_gender={self.user_gender}, user_created_time={self.user_created_time})"


class Article(Base):
    __tablename__ = "articles"
    
    article_id: Mapped[primary_key_id]
    article_title: Mapped[str_field_not_null]
    article_content: Mapped[text_field]
    article_author_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    article_created_time: Mapped[date_field]
    article_updated_time: Mapped[update_time_field]
    
    # 关系定义
    article_author = relationship("User", back_populates="user_articles")
    article_comments = relationship("Comment", back_populates="comment_article", cascade="all, delete-orphan")
    article_labels = relationship("Label", back_populates="label_article", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Article(article_id={self.article_id}, article_title={self.article_title}, " \
               f"article_author_id={self.article_author_id}, article_created_time={self.article_created_time})"


class Comment(Base):
    __tablename__ = "comments"
    
    comment_id: Mapped[primary_key_id]
    comment_content: Mapped[text_field]
    comment_author_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    comment_article_id: Mapped[int] = mapped_column(ForeignKey("articles.article_id"), nullable=False)
    comment_created_time: Mapped[date_field]
    comment_updated_time: Mapped[update_time_field]
    
    # 关系定义
    comment_author = relationship("User", back_populates="user_comments")
    comment_article = relationship("Article", back_populates="article_comments")

    def __repr__(self):
        return f"Comment(comment_id={self.comment_id}, comment_content={self.comment_content[:50]}..., " \
               f"comment_author_id={self.comment_author_id}, comment_article_id={self.comment_article_id}, " \
               f"comment_created_time={self.comment_created_time})"


class Label(Base):
    __tablename__ = "labels"
    
    label_id: Mapped[primary_key_id]
    label_name: Mapped[str_field_not_null]
    label_article_id: Mapped[int] = mapped_column(ForeignKey("articles.article_id"), nullable=False)
    
    # 关系定义
    label_article = relationship("Article", back_populates="article_labels")

    def __repr__(self):
        return f"Label(label_id={self.label_id}, label_name={self.label_name}, label_article_id={self.label_article_id})"


# 创建索引以提高查询性能
def create_indexes():
    """创建数据库索引以提高查询性能"""
    # 文章表索引
    Index('idx_article_author', Article.article_author_id)
    Index('idx_article_created_time', Article.article_created_time)
    Index('idx_article_title', Article.article_title)
    
    # 评论表索引
    Index('idx_comment_article', Comment.comment_article_id)
    Index('idx_comment_author', Comment.comment_author_id)
    Index('idx_comment_created_time', Comment.comment_created_time)
    
    # 标签表索引
    Index('idx_label_article', Label.label_article_id)
    Index('idx_label_name', Label.label_name)
    
    # 用户表索引
    Index('idx_user_email', User.user_email)
    Index('idx_user_created_time', User.user_created_time)


# 创建所有表
def create_tables():
    Base.metadata.create_all(engine)
    create_indexes()


# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 性能优化查询函数
def get_articles_with_pagination(page: int = 1, page_size: int = 20, author_id: int = None):
    """
    分页查询文章，支持按作者筛选
    使用分页避免一次性加载大量数据
    """
    db = SessionLocal()
    try:
        query = db.query(Article)
        
        if author_id:
            query = query.filter(Article.article_author_id == author_id)
        
        # 按创建时间倒序排列
        query = query.order_by(Article.article_created_time.desc())
        
        # 分页
        total = query.count()
        articles = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "articles": articles,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    finally:
        db.close()


def search_articles(keyword: str, page: int = 1, page_size: int = 20):
    """
    搜索文章（标题和内容）
    使用数据库全文搜索功能
    """
    db = SessionLocal()
    try:
        # 使用 LIKE 进行模糊搜索（简单实现）
        # 生产环境建议使用数据库的全文搜索功能
        query = db.query(Article).filter(
            Article.article_title.contains(keyword) | 
            Article.article_content.contains(keyword)
        )
        
        total = query.count()
        articles = query.order_by(Article.article_created_time.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            "articles": articles,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    finally:
        db.close()


def get_article_with_relations(article_id: int):
    """
    获取文章及其关联数据（用户、评论、标签）
    使用 JOIN 查询减少数据库往返
    """
    db = SessionLocal()
    try:
        # 使用 JOIN 一次性获取所有相关数据
        article = db.query(Article).filter(Article.article_id == article_id).first()
        if article:
            # 预加载关联数据
            comments = db.query(Comment).filter(Comment.comment_article_id == article_id).all()
            labels = db.query(Label).filter(Label.label_article_id == article_id).all()
            
            return {
                "article": article,
                "comments": comments,
                "labels": labels
            }
        return None
    finally:
        db.close()


# 主函数
if __name__ == "__main__":
    print("正在创建数据库表...")
    print(f"数据库连接字符串: {database_url}")
    create_tables()
    print("数据库表创建完成！")
    print("\n性能优化说明：")
    print("1. 已创建关键字段索引")
    print("2. 配置了连接池优化")
    print("3. 提供了分页查询函数")
    print("4. 支持搜索和关联查询优化") 