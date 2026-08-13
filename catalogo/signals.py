import json
import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from pywebpush import webpush, WebPushException

from .models import Produto, PushSubscription

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Produto)
def notificar_novo_produto(sender, instance, created, **kwargs):
    """
    Ao criar um Produto novo, envia push para todas as subscriptions
    ativas do Lojista dono desse produto.
    """
    if not created:
        return  # só notifica em criação, não em edição

    lojista = instance.lojista
    subscriptions = PushSubscription.objects.filter(lojista=lojista, ativo=True)

    if not subscriptions.exists():
        return

    payload = json.dumps({
        "title": f"Novidade na {lojista.nome_loja}!",
        "body": f"{instance.nome} acabou de chegar. Confira agora.",
        "url": f"/{lojista.slug}/",
        "tag": f"produto-{instance.pk}",
    })

    for subscription in subscriptions:
        try:
            webpush(
                subscription_info=subscription.to_subscription_info(),
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY_PATH,
                vapid_claims=settings.VAPID_CLAIMS,
            )
        except WebPushException as e:
            logger.warning(f"Push falhou para {subscription.endpoint[:50]}: {e}")
            if e.response is not None and e.response.status_code in (404, 410):
                subscription.ativo = False
                subscription.save(update_fields=["ativo"])