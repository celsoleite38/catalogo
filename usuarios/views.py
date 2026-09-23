from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.text import slugify

from catalogo.models import Lojista
from catalogo.views import slug_unico
from .forms import CadastroForm, PerfilForm

User = get_user_model()
LOJISTA_SUBJECT = 'Confirme seu cadastro no Catálogo Digital'


def _enviar_email_confirmacao(request, user):
    """Gera o token e envia o email com o link de confirmação."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = request.build_absolute_uri(
        reverse('usuarios:confirmar', args=[uid, token])
    )

    corpo = f"""Olá!

Recebemos o seu cadastro no Catálogo Digital. Para confirmar o seu email e
ativar sua conta, clique no link abaixo:

{link}

Se você não criou esta conta, ignore este email.
"""
    corpo_html = f"""
<p>Olá!</p>
<p>Recebemos o seu cadastro no Catálogo Digital. Para confirmar o seu email e
ativar sua conta, clique no botão abaixo:</p>
<p><a href="{link}" style="display:inline-block;background:#15803d;color:#ffffff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;">Confirmar meu cadastro</a></p>
<p>Se o botão não funcionar, copie e cole este link no navegador:<br>
<small>{link}</small></p>
<p>Se você não criou esta conta, ignore este email.</p>
"""
    email = EmailMultiAlternatives(
        LOJISTA_SUBJECT,
        corpo,
        to=[user.email],
    )
    email.attach_alternative(corpo_html, 'text/html')
    email.send(fail_silently=False)


def cadastro(request):
    if request.user.is_authenticated:
        return redirect('catalogo:painel_lojista')

    if request.method == 'POST':
        form = CadastroForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            senha = form.cleaned_data['senha']
            user = User.objects.create_user(
                username=email,
                email=email,
                password=senha,
                is_active=False,
            )
            try:
                _enviar_email_confirmacao(request, user)
                email_enviado = True
            except Exception:
                email_enviado = False
            return render(request, 'usuarios/confirmacao_enviada.html', {
                'email': email,
                'email_enviado': email_enviado,
            })
    else:
        form = CadastroForm()

    return render(request, 'usuarios/cadastro.html', {'form': form})


def confirmar_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])
        messages.success(
            request,
            'Email confirmado com sucesso! Agora você pode fazer login.',
        )
        return redirect('catalogo:login')

    return render(request, 'usuarios/confirmacao_invalida.html')


def reenviar_confirmacao(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        usuario = User.objects.filter(email=email).first()
        if usuario and not usuario.is_active:
            try:
                _enviar_email_confirmacao(request, usuario)
            except Exception:
                messages.error(
                    request,
                    'Não foi possível enviar o email agora. Verifique o SMTP e tente novamente.',
                )
                return redirect('usuarios:reenviar')
            return render(request, 'usuarios/confirmacao_enviada.html', {'email': email})
        # Mesma resposta para emails inexistentes (evita revelar contas)
        return render(request, 'usuarios/confirmacao_enviada.html', {'email': email})

    return render(request, 'usuarios/reenviar.html')


def _perfil_completo(lojista):
    if not lojista:
        return False
    return all([
        lojista.nome_loja,
        lojista.cnpj,
        lojista.whatsapp,
    ]) and bool(lojista.logo)


@login_required
def perfil(request):
    if request.user.is_superuser:
        return redirect('catalogo:admin_painel')

    lojista = request.user.lojas.first() or None
    logo_obrigatoria = not (lojista and bool(lojista.logo))

    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, logo_obrigatoria=logo_obrigatoria)
        if form.is_valid():
            if lojista is None:
                lojista = Lojista(user=request.user)

            lojista.nome_loja = form.cleaned_data['nome_loja']
            lojista.cnpj = form.cleaned_data['cnpj']
            lojista.whatsapp = form.cleaned_data['whatsapp']

            if form.cleaned_data['logo']:
                if lojista.logo:
                    lojista.logo.delete(save=False)
                lojista.logo = form.cleaned_data['logo']

            if not lojista.slug:
                lojista.slug = slug_unico(slugify(lojista.nome_loja))

            lojista.save()
            messages.success(request, 'Perfil da loja salvo com sucesso!')
            return redirect('catalogo:painel_lojista')
    else:
        initial = {
            'nome_loja': lojista.nome_loja if lojista else '',
            'cnpj': lojista.cnpj if lojista else '',
            'whatsapp': lojista.whatsapp if lojista else '',
        }
        form = PerfilForm(initial=initial)

    return render(request, 'usuarios/perfil.html', {
        'form': form,
        'lojista': lojista,
    })