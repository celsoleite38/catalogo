from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('cadastro/', views.cadastro, name='cadastro'),
    path('confirmar/<uidb64>/<token>/', views.confirmar_email, name='confirmar'),
    path('reenviar/', views.reenviar_confirmacao, name='reenviar'),
    path('perfil/', views.perfil, name='perfil'),

    # Recuperação de senha
    path('esqueci-senha/', auth_views.PasswordResetView.as_view(
        template_name='usuarios/password_reset_form.html',
        email_template_name='usuarios/password_reset_email.html',
        html_email_template_name='usuarios/password_reset_email_html.html',
        subject_template_name='usuarios/password_reset_subject.txt',
        success_url=reverse_lazy('usuarios:password_reset_done'),
    ), name='password_reset'),
    path('esqueci-senha/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='usuarios/password_reset_done.html',
    ), name='password_reset_done'),
    path('esqueci-senha/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='usuarios/password_reset_confirm.html',
        success_url=reverse_lazy('usuarios:password_reset_complete'),
    ), name='password_reset_confirm'),
    path('esqueci-senha/concluido/', auth_views.PasswordResetCompleteView.as_view(
        template_name='usuarios/password_reset_complete.html',
    ), name='password_reset_complete'),
]