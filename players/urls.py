from django.urls import path
from . import views

urlpatterns = [
        path('', views.index, name='index'),
        path('<str:room_name>/', views.index, name='index'),
        path('<str:room_name>/ajax/', views.ajax, name='ajax'),
        path('rolls/<uuid:roll_id>/', views.rolls, name='rolls')
]

