"""Controle de acesso das telas do painel do lojista.

A Central de Cobranças é a fonte da verdade: enquanto ela responder
`ativa` ou `trial`, o lojista usa o painel normalmente. Sem isso, ele é
levado à tela de planos para assinar.
"""
import threading
from datetime import date
from functools import wraps

from django.shortcuts import redirect

from .models import Lojista
from planos.services import central_client


def _trial_local_valido(lojista):
    return (
        lojista
        and lojista.status_assinatura == 'trial'
        and lojista.trial_fim
        and lojista.trial_fim >= date.today()
    )


def _sincronizar_pagamento(lojista):
    """A Central confirmou pagamento e a loja local ainda não sabe.

    A Central nunca avisa o catálogo (não existe callback no fluxo de
    pagamento), então quem paga só volta a ter vitrine depois de o próprio
    lojista passar pelo painel. Aqui a vitrine volta sozinha.
    """
    if not lojista or (lojista.status_assinatura == 'ativa' and lojista.ativo):
        return
    Lojista.objects.filter(pk=lojista.pk).update(
        status_assinatura='ativa',
        trial_fim=None,
        ativo=True,
    )


def require_acesso(view_func):
    """Libera a view apenas para assinante/trial; senão manda para os planos."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        lojista = Lojista.objects.filter(user=request.user).first()
        acesso = central_client.verificar_acesso(request.user.email)
        status = (acesso or {}).get('status')

        if status in ('ativa', 'trial'):
            if status == 'ativa':
                _sincronizar_pagamento(lojista)
            return view_func(request, *args, **kwargs)

        if _trial_local_valido(lojista):
            # Trial válido aqui, mas ausente na Central (thread do cadastro
            # pode ter falhado): re-registra em segundo plano e libera.
            if status in (None, 'sem_assinatura'):
                threading.Thread(
                    target=central_client.registrar_trial,
                    args=(request.user.email, lojista.nome_loja),
                    daemon=True,
                ).start()
            return view_func(request, *args, **kwargs)

        if acesso is None and lojista and lojista.status_assinatura == 'ativa':
            # Central fora do ar: não tranca quem já paga.
            return view_func(request, *args, **kwargs)

        return redirect('planos:pagina_planos')

    return _wrapped
