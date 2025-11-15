from django.urls import path
from . import views

app_name = 'llamadas'

urlpatterns = [
    path('', views.index, name='index'),
    path('iniciar/', views.iniciar_llamada, name='iniciar_llamada'),
    path('webhook/', views.webhook_llamada, name='webhook_llamada'),
    path('webhook-test/', views.webhook_test, name='webhook_test'),
    path('webhook-status/', views.webhook_status, name='webhook_status'),
    path('llamada/<int:llamada_id>/', views.detalle_llamada, name='detalle_llamada'),
]

