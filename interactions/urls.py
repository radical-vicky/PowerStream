from django.urls import path
from . import views

app_name = 'interactions'

urlpatterns = [
    path('tip/<str:username>/', views.tip_user, name='tip'),
    path('tip/success/<int:tip_id>/', views.tip_success, name='tip_success'),
    path('history/', views.tipping_history, name='tipping_history'),  # Add this line
]