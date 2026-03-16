from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<int:conversation_id>/', views.conversation_detail, name='conversation'),
    path('start/<str:username>/', views.start_conversation, name='start'),
    path('ajax/<int:conversation_id>/send/', views.send_message_ajax, name='send_message_ajax'),
    path('ajax/<int:conversation_id>/messages/', views.get_messages_ajax, name='get_messages_ajax'),
    path('ajax/unread/', views.get_unread_count, name='unread_count'),
]