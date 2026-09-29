from django.contrib import admin

from .models import Plano

try:
    from planos.services import central_client
except Exception:  # pragma: no cover
    central_client = None


def sincronizar_central():
    """Envia todos os planos para a Central de Cobranças (cria/atualiza)."""
    try:
        planos = [
            {
                'codigo': p.codigo,
                'nome': p.nome,
                'descricao': p.descricao,
                'valor': float(p.valor),
                'ciclo': p.ciclo,
                'dias_trial': p.dias_trial,
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
    list_display = ('codigo', 'nome', 'valor', 'ciclo', 'dias_trial', 'ordem', 'ativo')
    list_editable = ('ativo', 'ordem')
    list_filter = ('ativo', 'ciclo')
    search_fields = ('nome', 'codigo')
    list_display_links = ('codigo', 'nome')
    prepopulated_fields = {'codigo': ('nome',)}