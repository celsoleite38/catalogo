from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Plano, ConfiguracaoGlobal

from .admin import sincronizar_central


@receiver(post_save, sender=Plano)
def plano_salvo(sender, instance, **kwargs):
    sincronizar_central()


@receiver(post_delete, sender=Plano)
def plano_removido(sender, instance, **kwargs):
    sincronizar_central()


@receiver(post_save, sender=ConfiguracaoGlobal)
def config_global_salva(sender, instance, **kwargs):
    sincronizar_central()