from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_planos, name='pagina_planos'),
    path('checkout/<str:plano_codigo>/', views.checkout, name='checkout'),
    path('obrigado/', views.pagina_obrigado, name='pagina_obrigado'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('webhook/central/', views.webhook_central, name='webhook_central'),
]