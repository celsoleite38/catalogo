from django.contrib import admin
from .models import Lojista, Categoria, Produto, VariacaoProduto, TipoVariacao, ValorVariacao

class VariacaoInline(admin.TabularInline):
    model = VariacaoProduto
    extra = 1

class CategoriaInline(admin.TabularInline):
    model = Categoria
    extra = 1

@admin.register(Lojista)
class LojistaAdmin(admin.ModelAdmin):
    list_display = ('nome_loja', 'slug', 'whatsapp', 'user')
    prepopulated_fields = {'slug': ('nome_loja',)}
    inlines = [CategoriaInline]

@admin.register(TipoVariacao)
class TipoVariacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'lojista')
    list_filter = ('lojista',)

@admin.register(ValorVariacao)
class ValorVariacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'tipo_lojista')
    list_filter = ('tipo__lojista',)

    @admin.display(description='Lojista')
    def tipo_lojista(self, obj):
        return obj.tipo.lojista.nome_loja

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'lojista', 'ordem')
    list_filter = ('lojista',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(lojista__user=request.user)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.lojista = request.user.lojas.first()
        super().save_model(request, obj, form, change)

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'preco_base', 'ativo', 'get_lojista')
    list_filter = ('categoria__lojista', 'ativo')
    search_fields = ('nome', 'descricao')
    inlines = [VariacaoInline]

    @admin.display(description='Lojista')
    def get_lojista(self, obj):
        return obj.lojista.nome_loja if obj.lojista else "-"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(lojista__user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "categoria" and not request.user.is_superuser:
            kwargs["queryset"] = Categoria.objects.filter(lojista__user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.lojista = request.user.lojas.first()
        else:
            # Se for superusuario cadastrando o produto, atrela o lojista dono da categoria
            if obj.categoria and not getattr(obj, 'lojista', None):
                obj.lojista = obj.categoria.lojista
        super().save_model(request, obj, form, change)