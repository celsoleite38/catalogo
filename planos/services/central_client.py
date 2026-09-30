"""Cliente HTTP para a Central de Cobranças.

Qualquer sistema usa o mesmo código: configura CENTRAL_URL, CENTRAL_SISTEMA
e CENTRAL_TOKEN no .env e as páginas de planos/checkout funcionam idênticas.
"""
import requests
from django.conf import settings


def _base_url():
    return settings.CENTRAL_URL.rstrip('/')


def _headers():
    return {
        "X-Central-Token": settings.CENTRAL_TOKEN,
        "Content-Type": "application/json",
    }


def _get(caminho, params=None):
    r = requests.get(
        _base_url() + caminho,
        params=params or {},
        headers=_headers(),
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def _post(caminho, dados):
    dados = dict(dados)
    dados['sistema'] = settings.CENTRAL_SISTEMA
    r = requests.post(
        _base_url() + caminho,
        json=dados,
        headers=_headers(),
        timeout=30,
    )
    return r.json(), r.status_code


def listar_planos():
    """Lista os planos do catálogo (cadastrados no admin local, já sincronizados
    com a Central pela mesma API de plano do sistema)."""
    from planos.models import Plano
    return [
        {
            'codigo': p.codigo,
            'nome': p.nome,
            'descricao': p.descricao,
            'valor': str(p.valor),
            'ciclo': p.ciclo,
            'dias_trial': p.dias_trial,
            'ativo': p.ativo,
        }
        for p in Plano.objects.filter(ativo=True)
    ]


def upsert_planos(planos):
    """Sincroniza (cria/atualiza) os planos do sistema na Central."""
    return _post('/api/planos/', {'planos': planos})


def criar_checkout(plano_codigo, email, nome='', cpf_cnpj='', recorrente=True,
                   url_sucesso='', url_cancelamento='', dias_vigor=None, referencia=''):
    """Cria o checkout na Central e retorna (json, status)."""
    dados = {
        'plano': plano_codigo,
        'email': email,
        'nome': nome,
        'cpf_cnpj': cpf_cnpj,
        'recorrente': recorrente,
        'url_sucesso': url_sucesso,
        'url_cancelamento': url_cancelamento,
        'referencia': referencia,
    }
    if dias_vigor:
        dados['dias_vigor'] = dias_vigor
    return _post('/api/checkout/', dados)


def verificar_acesso(email):
    """Pergunta à Central se o e-mail tem acesso liberado."""
    try:
        return _get(
            '/api/verificar-acesso/',
            {'sistema': settings.CENTRAL_SISTEMA, 'email': email},
        )
    except requests.RequestException:
        return None


def registrar_trial(email, nome=''):
    """Registra a assinatura de trial do usuário na Central (idempotente).

    Usa o plano de referência como base; a Central aplica o próprio
    dias_trial do plano. Chamada de forma assíncrona pelos fluxos de cadastro.
    """
    try:
        from .trial import plano_referencia
        plano = plano_referencia()
        return _post('/api/criar-assinatura/', {
            'email': email,
            'plano': plano.codigo if plano else 'anual',
            'nome': nome or '',
        })
    except requests.RequestException:
        return None, 0


def registrar_venda(valor_total, valor_comissao=0, email='', dados=None):
    """Reporta uma venda à Central (sistemas do tipo VENDA)."""
    payload = {
        'valor_total': valor_total,
        'valor_comissao': valor_comissao,
        'email': email,
        'dados_extras': dados or {},
    }
    return _post('/api/registrar-venda/', payload)