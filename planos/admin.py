from django.contrib import admin

from .models import Plano, ConfiguracaoGlobal

try:
    from planos.services import central_client
except Exception:  # pragma: no cover
    central_client = None


def sincronizar_central():
    """Envia todos os planos para a Central de Cobranças (cria/atualiza).

    A Central recebe sempre o mesmo `dias_trial`: o valor global da
    ConfiguracaoGlobal (trial único para todos os planos).
    """
    try:
        from planos.services.trial import dias_trial as dias_trial_global
        dias = dias_trial_global()
        planos = [
            {
                'codigo': p.codigo,
                'nome': p.nome,
                'descricao': p.descricao,
                'valor': float(p.valor),
                'ciclo': p.ciclo,
                'dias_trial': dias,
                'ativo': p.ativo,
            }
            for p in Plano.objects.all()
        ]
        if central_client:
            central_client.upsert_planos(planos)
            return True
    except Exception:
        pass
    return False


@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'valor', 'ciclo', 'ordem', 'ativo')
    list_editable = ('ativo', 'ordem')
    list_filter = ('ativo', 'ciclo')
    search_fields = ('nome', 'codigo')
    list_display_links = ('codigo', 'nome')
    prepopulated_fields = {'codigo': ('nome',)}


@admin.register(ConfiguracaoGlobal)
class ConfiguracaoGlobalAdmin(admin.ModelAdmin):
    """Configuração global (uma única linha): o trial é editado aqui."""
    list_display = ('id', 'dias_trial')
    fields = ('dias_trial',)

    def has_add_permission(self, request):
        return not ConfiguracaoGlobal.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False