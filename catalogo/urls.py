from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    # Login e Logout do Lojista
    path('login/', views.LoginView.as_view(template_name='painel/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='painel/login.html'), name='logout'),
    
    # Painel do Lojista
    path('painel/', views.painel_lojista, name='painel_lojista'),
    path('painel/configuracoes/', views.configuracoes_lojista, name='configuracoes_lojista'),
    path('painel/produtos/novo/', views.cadastrar_produto, name='cadastrar_produto'),
    path('painel/categorias/nova/', views.cadastrar_categoria, name='cadastrar_categoria'),
    path('painel/variacoes/', views.gerenciar_variacoes, name='gerenciar_variacoes'),
    path('painel/variacoes/<int:pk>/excluir/', views.excluir_tipo_variacao, name='excluir_tipo_variacao'),
    path('painel/variacoes/valores/<int:pk>/excluir/', views.excluir_valor_variacao, name='excluir_valor_variacao'),

    # Painel Admin (Superusuário)
    path('admin-painel/', views.admin_painel, name='admin_painel'),
    path('admin-painel/usuarios/', views.admin_usuarios, name='admin_usuarios'),
    path('admin-painel/usuarios/novo/', views.admin_usuario_novo, name='admin_usuario_novo'),
    path('admin-painel/usuarios/<int:pk>/desativar/', views.admin_usuario_desativar, name='admin_usuario_desativar'),
    path('admin-painel/lojas/nova/', views.admin_loja_nova, name='admin_loja_nova'),
    path('admin-painel/lojas/<int:pk>/editar/', views.admin_loja_editar, name='admin_loja_editar'),
    path('admin-painel/lojas/<int:pk>/desativar/', views.admin_loja_desativar, name='admin_loja_desativar'),
    path('admin-painel/lojas/<int:pk>/excluir/', views.admin_loja_excluir, name='admin_loja_excluir'),

    path('produtos/<int:pk>/editar/', views.editar_produto, name='editar_produto'),

    # PWA (precisa vir antes do catch-all de slug)
    path('sw.js', views.service_worker, name='service_worker'),
    path('<slug:slug>/manifest.json', views.manifest_json, name='manifest'),
    path('<slug:slug>/icone/<int:tamanho>/', views.pwa_icon, name='pwa_icon'),
    path('<slug:slug>/instalar/', views.instalar_app, name='instalar_app'),

    # Catálogo público (Mantenha no final das rotas)
    path('<slug:slug>/', views.ver_catalogo, name='catalogo'),
]