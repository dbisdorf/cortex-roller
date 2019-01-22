from django.urls import path
from . import views

urlpatterns = [
        path('', views.index, name='index'),
        path('purge/', views.purge, name='purge'),
        path('random/', views.random_report, name='random'),
        path('<str:room_name>/', views.index, name='index'),
        path('<str:room_name>/ajax/', views.ajax, name='ajax'),
        path('rolls/<uuid:roll_id>/', views.rolls, name='rolls')
]
