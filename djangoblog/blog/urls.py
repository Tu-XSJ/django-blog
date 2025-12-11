from django.urls import path
from . import views

urlpatterns = [
    # 页面
    path('article/<int:article_id>/', views.article_view),
    # 接口
    path('api/article/<int:article_id>/stats/', views.ArticleView.as_view()),
]