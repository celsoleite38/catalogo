"""Regras do período de teste (trial) do catálogo.

Os dias de trial saem do admin de Planos (campo `dias_trial` do plano).
`dias_trial = 0` significa "sem trial": o lojista vai direto para o
pagamento e o acesso só é liberado depois da confirmação.
"""
from datetime import date, timedelta


def plano_referencia():
    """Plano usado como referência para o trial (o mais barato ativo)."""
    from ..models import Plano
    return Plano.objects.filter(ativo=True).order_by('valor', 'ordem').first()


def dias_trial():
    """Quantos dias de teste, conforme definido no admin de Planos."""
    plano = plano_referencia()
    return int(plano.dias_trial or 0) if plano else 0


def data_fim_trial():
    """Data de fim do trial a partir de hoje, ou None quando não há trial."""
    dias = dias_trial()
    if dias <= 0:
        return None
    return date.today() + timedelta(days=dias)


def dias_restantes(lojista):
    """Dias que faltam para o trial acabar (0 já venceu, None se não há trial)."""
    if not lojista or not lojista.trial_fim:
        return None
    return (lojista.trial_fim - date.today()).days
