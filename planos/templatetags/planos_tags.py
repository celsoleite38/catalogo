"""Tags de template do app planos."""
from django import template

from ..services.trial import dias_restantes

register = template.Library()

DIAS_AVISO_BANNER = 5


@register.inclusion_tag('planos/_aviso_trial.html', takes_context=True)
def aviso_trial(context):
    """Banner de contagem regressiva do trial (do D-5 até o D-1)."""
    request = context.get('request')
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or user.is_superuser:
        return {'mostrar': False}

    lojista = user.lojas.first()
    if not lojista or lojista.status_assinatura != 'trial':
        return {'mostrar': False}

    dias = dias_restantes(lojista)
    if dias is None or dias < 1 or dias > DIAS_AVISO_BANNER:
        return {'mostrar': False}

    return {
        'mostrar': True,
        'dias': dias,
        'trial_fim': lojista.trial_fim,
        'urgente': dias <= 1,
    }


@register.inclusion_tag('planos/_banner_assinatura.html', takes_context=True)
def aviso_assinatura(context):
    """Banner quando a vitrine está offline (trial vencido, sem assinatura ou
    pagamento cancelado), mesmo que o painel esteja liberado pela Central."""
    request = context.get('request')
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or user.is_superuser:
        return {'mostrar': False}

    lojista = user.lojas.first()
    if not lojista:
        return {'mostrar': False}
    if lojista.ativo and lojista.esta_com_acesso_liberado():
        return {'mostrar': False}

    return {'mostrar': True, 'lojista': lojista}
