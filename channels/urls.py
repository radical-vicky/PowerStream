from django.urls import path
from . import views

app_name = 'channels'

urlpatterns = [
    path('', views.channel_list, name='list'),
    path('create/', views.channel_create, name='create'),
    path('<slug:slug>/', views.channel_detail, name='detail'),
    path('<slug:slug>/edit/', views.channel_edit, name='edit'),
    path('<slug:slug>/delete/', views.channel_delete, name='delete'),  # Add this line
    path('<slug:slug>/subscribe/', views.subscribe_channel, name='subscribe'),
    path('<slug:slug>/suggest/', views.suggest_post, name='suggest_post'),
    path('suggestion/<int:pk>/review/', views.review_suggestion, name='review_suggestion'),
    path('suggestion/<int:pk>/fund/', views.fund_suggestion, name='fund_suggestion'),
]