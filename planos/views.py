import json
import logging

import requests
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model

from .services import central_client
from catalogo.models import Lojista

logger = logging.getLogger(__name__)
User = get_user_model()


@login_required
def pagina_planos(request):
    planos = []
    erro = None
    try:
        planos = central_client.listar_planos()
    except requests.RequestException as e:
        logger.exception("Erro ao buscar planos na Central")
        erro = 'Não foi possível carregar os planos. Tente novamente em instantes.'

    status_acesso = None
    if request.user.email:
        acesso = central_client.verificar_acesso(request.user.email)
        if acesso:
            status_acesso = acesso.get('status')

    return render(request, 'planos/pagina_planos.html', {
        'planos': planos,
        'erro': erro,
        'status_acesso': status_acesso,
    })


@login_required
def checkout(request, plano_codigo):
    planos = []
    erro = None
    try:
        planos = central_client.listar_planos()
    except requests.RequestException:
        planos = []
    plano = next((p for p in planos if p['codigo'] == plano_codigo), None)
    if not plano:
        return redirect('planos:pagina_planos')

    if request.method == 'POST':
        email = request.user.email
        nome = request.POST.get('nome', '').strip()
        cpf_cnpj = request.POST.get('cpf_cnpj', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        if not telefone:
            loja_ref = request.user.lojas.filter(whatsapp__isnull=False).first()
            telefone = (loja_ref.whatsapp if loja_ref else '') or ''

        if not email:
            erro = 'Informe o e-mail para o pagamento.'
        else:
            url_sucesso = request.build_absolute_uri(reverse('planos:pagina_obrigado'))
            url_cancelamento = request.build_absolute_uri(reverse('planos:pagina_planos'))
            try:
                resultado, status = central_client.criar_checkout(
                    plano_codigo=plano_codigo,
                    email=email,
                    nome=nome or request.user.get_full_name(),
                    cpf_cnpj=cpf_cnpj,
                    telefone=telefone,
                    recorrente=True,
                    url_sucesso=url_sucesso,
                    url_cancelamento=url_cancelamento,
                )
            except (requests.RequestException, ValueError, TypeError) as e:
                logger.error(
                    'checkout falhou ao chamar a Central (plano=%s email=%s): %s',
                    plano_codigo, email, e,
                )
                resultado, status = None, 0
            if status == 200 and resultado and resultado.get('link'):
                return redirect(resultado['link'])
            erro = (resultado or {}).get('erro') or 'Não foi possível gerar o pagamento. Tente novamente em instantes.'

    loja_ref = request.user.lojas.filter(whatsapp__isnull=False).first()
    return render(request, 'planos/checkout.html', {
        'plano': plano,
        'erro': erro,
        'telefone_inicial': (loja_ref.whatsapp if loja_ref else '') or '',
    })


@login_required
def pagina_obrigado(request):
    ativa = False
    if request.user.is_authenticated:
        try:
            acesso = central_client.verificar_acesso(request.user.email)
            ativa = bool(acesso and acesso.get('pode_acessar'))
        except requests.RequestException:
            ativa = False
    return render(request, 'planos/obrigado.html', {'ativa': ativa})


@login_required
def dashboard(request):
    lojas = Lojista.objects.filter(user=request.user)
    acesso = None
    if request.user.email:
        acesso = central_client.verificar_acesso(request.user.email)
    return render(request, 'planos/dashboard.html', {
        'lojas': lojas,
        'acesso': acesso,
    })


@csrf_exempt
def webhook_central(request):
    """Recebe o aviso da Central quando o status da assinatura muda.

    Exige o mesmo token que o catálogo usa para chamar a Central: sem ele,
    qualquer POST forjado reativa a vitrine de uma loja cancelada.
    """
    if request.method != 'POST':
        return JsonResponse({'erro': 'Use POST'}, status=405)
    if not central_client.token_valido(
        request.headers.get('X-Central-Token', '')
    ):
        logger.warning('webhook da Central com token inválido')
        return JsonResponse({'erro': 'Token inválido'}, status=401)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'erro': 'JSON inválido'}, status=400)

    assinatura = data.get('assinatura') or {}
    email = assinatura.get('email', '')
    status = assinatura.get('status', '')
    vencimento = assinatura.get('proximo_vencimento')

    if not email:
        logger.warning('webhook recebido sem e-mail')
        return JsonResponse({'ok': True, 'aviso': 'sem e-mail'})

    if status == 'ativa':
        usuarios = User.objects.filter(email=email)
        atualizadas = 0
        for usuario in usuarios:
            atualizadas += Lojista.objects.filter(user=usuario).update(
                status_assinatura='ativa',
                trial_fim=vencimento,
                ativo=True,  # pagamento confirmado: vitrine pública volta
            )
        logger.info('webhook status=ativa email=%s vencimento=%s lojas=%d', email, vencimento, atualizadas)
        return JsonResponse({'ok': True, 'lojas_atualizadas': atualizadas})

    if status in ('cancelada', 'inativa'):
        usuarios = User.objects.filter(email=email)
        atualizadas = 0
        for usuario in usuarios:
            atualizadas += Lojista.objects.filter(user=usuario).update(
                status_assinatura=status,
                ativo=False,
            )
        logger.info('webhook status=%s email=%s lojas=%d', status, email, atualizadas)
        return JsonResponse({'ok': True, 'lojas_atualizadas': atualizadas})

    if status == 'atrasada':
        usuarios = User.objects.filter(email=email)
        atualizadas = 0
        for usuario in usuarios:
            atualizadas += Lojista.objects.filter(user=usuario).update(
                status_assinatura='atrasada',
                ativo=False,
            )
        logger.info('webhook status=atrasada email=%s lojas=%d', email, atualizadas)
        return JsonResponse({'ok': True, 'lojas_atualizadas': atualizadas})

    logger.info('webhook status=%s email=%s ignorado', status, email)
    return JsonResponse({'ok': True, 'aviso': 'status ignorado'})