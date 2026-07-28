from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    # Login e Logout do Lojista
    path('login/', auth_views.LoginView.as_view(template_name='painel/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='painel/login.html'), name='logout'),
    
    # Painel do Lojista
    path('painel/', views.painel_lojista, name='painel_lojista'),
    path('painel/configuracoes/', views.configuracoes_lojista, name='configuracoes_lojista'),
    path('painel/produtos/novo/', views.cadastrar_produto, name='cadastrar_produto'),
    path('painel/categorias/nova/', views.cadastrar_categoria, name='cadastrar_categoria'),

    path('produtos/<int:pk>/editar/', views.editar_produto, name='editar_produto'),

    # Catálogo público (Mantenha no final das rotas)
    path('<slug:slug>/', views.ver_catalogo, name='catalogo'),
]