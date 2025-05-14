from django.urls import path
from . import views

app_name = 'downloader'

urlpatterns = [
    path('', views.index, name='index'),
    path('get_video_info/', views.get_video_info, name='get_video_info'),
    path('download/', views.download, name='download'),
    path('check_progress/', views.check_progress, name='check_progress'),
]
