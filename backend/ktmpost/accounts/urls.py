from django.urls import path
from .views import (
    CheckAuthView, LoginView, LogoutView, WriterListCreateView, WriterDetailView,
    CategoryListCreateView, CategoryDetailView, ArticleListCreateView, ArticleDetailView,
    ArticleStatsView, UploadView, VideoCategoryListCreateView, VideoListCreateView, VideoDetailView, VideoLiveView, VideoUploadView  

)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('check-auth/', CheckAuthView.as_view(), name='check-auth'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('writers/', WriterListCreateView.as_view(), name='writer-list-create'),
    path('writers/<int:pk>/', WriterDetailView.as_view(), name='writer-detail'),
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('articles/', ArticleListCreateView.as_view(), name='article-list-create'),
    path('articles/<int:pk>/', ArticleDetailView.as_view(), name='article-detail'),
    path('article-stats/', ArticleStatsView.as_view(), name='article-stats'),
    path('upload/', UploadView.as_view(), name='upload'),
    path('video-categories/', VideoCategoryListCreateView.as_view(), name='video-category-list-create'),
    path('videos/', VideoListCreateView.as_view(), name='video-list-create'),
    path('videos/<int:pk>/', VideoDetailView.as_view(), name='video-detail'),
    path('videos/<int:pk>/live/', VideoLiveView.as_view(), name='video-live'),
    path('upload/video/', VideoUploadView.as_view(), name='video-upload'),

]