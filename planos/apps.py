from django.apps import AppConfig


class PlanosConfig(AppConfig):
    name = 'planos'
    verbose_name = 'Planos e Assinaturas'

    def ready(self):
        import planos.signals  # noqa: F401