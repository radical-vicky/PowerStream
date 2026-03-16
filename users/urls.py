from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('<str:username>/', views.profile, name='profile'),
    path('<str:username>/edit/', views.profile_edit, name='profile_edit'),
    path('<str:username>/follow/', views.follow_user, name='follow'),
    path('<str:username>/followers/', views.followers_list, name='followers'),
    path('<str:username>/following/', views.following_list, name='following'),
]