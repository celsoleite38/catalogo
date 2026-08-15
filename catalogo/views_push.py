import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Lojista, PushSubscription
from .utils_push import get_vapid_public_key_urlsafe

def vapid_public_key(request, slug):
    return JsonResponse({"publicKey": get_vapid_public_key_urlsafe()})


@csrf_exempt
@require_POST
def push_subscribe(request, slug):
    """
    Recebe a subscription gerada pelo pushManager.subscribe() no navegador
    e salva vinculada ao Lojista identificado pelo slug da URL.
    """
    lojista = get_object_or_404(Lojista, slug=slug, ativo=True, notificacoes_habilitadas=True)

    try:
        data = json.loads(request.body)
        endpoint = data["endpoint"]
        p256dh = data["keys"]["p256dh"]
        auth = data["keys"]["auth"]
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({"error": "payload inválido"}, status=400)

    subscription, created = PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "lojista": lojista,
            "p256dh": p256dh,
            "auth": auth,
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:255],
            "ativo": True,
        }
    )

    return JsonResponse({"status": "ok", "created": created})


@csrf_exempt
@require_POST
def push_unsubscribe(request, slug):
    """Chamado quando o usuário desativa notificações ou o navegador invalida o endpoint."""
    try:
        data = json.loads(request.body)
        endpoint = data["endpoint"]
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({"error": "payload inválido"}, status=400)

    PushSubscription.objects.filter(endpoint=endpoint).delete()
    return JsonResponse({"status": "ok"})