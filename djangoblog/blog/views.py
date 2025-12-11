from django.shortcuts import render,get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_GET
from .models import Article
from .services import ReadAndSaveService

def article_view(request,article_id):
    article = get_object_or_404(Article,pk=article_id)
    return render(request,'blog/article.html',{'article':article})

class ArticleView(View):
    def get(self,request,article_id):
        """
        GET /api/article/<id>/stats/?user_id=xxx
        """
        user_id = request.GET.get('user_id','guest')

        service = ReadAndSaveService(article_id)

        service.record_view(user_id)

        current_views = service.get_stats()

        return JsonResponse({
            'code': 200,
            'msg': 'success',
            'data': {
                'views': current_views,
                'user_id': user_id,  # 把 user_id 也返回去，方便调试
                'article_id': article_id
            }
        })