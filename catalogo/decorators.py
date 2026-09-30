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
