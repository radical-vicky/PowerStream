from django.urls import path
from . import views

app_name = 'videos'

urlpatterns = [
    path('', views.video_list, name='list'),
    path('my-videos/', views.my_videos, name='my_videos'),
    path('liked/', views.liked_videos, name='liked'),
    path('upload/', views.video_upload, name='upload'),
    path('<int:pk>/', views.VideoDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.video_edit, name='edit'),
    path('<int:pk>/delete/', views.video_delete, name='delete'),
    path('<int:video_id>/like/', views.like_video, name='like'),
    path('<int:video_id>/comment/', views.add_comment, name='add_comment'),
    path('<int:video_id>/share/', views.share_video, name='share'),
]