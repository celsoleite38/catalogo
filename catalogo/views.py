from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView as AuthLoginView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.urls import reverse_lazy
from django.utils.text import slugify
from django import forms
from .models import Produto, Categoria, VariacaoProduto, Lojista, TipoVariacao, ValorVariacao
from .forms import ProdutoForm, CategoriaForm, ConfiguracaoLojistaForm, TipoVariacaoForm
from django.contrib import messages
from .themes import TEMAS, get_tema


def slug_unico(base_slug, instance=None):
    slug = base_slug
    contador = 1
    qs = Lojista.objects.filter(slug=slug)
    if instance:
        qs = qs.exclude(pk=instance.pk)
    while qs.exists():
        slug = f"{base_slug}-{contador}"
        qs = Lojista.objects.filter(slug=slug)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        contador += 1
    return slug


class LoginForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            try:
                user = User.objects.get_by_natural_key(username)
            except User.DoesNotExist:
                self.user_cache = None
            else:
                if not user.is_active:
                    raise forms.ValidationError(
                        'Desativado contate o administrador.',
                        code='inactive',
                    )
                self.user_cache = authenticate(self.request, username=username, password=password)

            if self.user_cache is None:
                raise self.get_invalid_login_error()

        return self.cleaned_data


class LoginView(AuthLoginView):
    form_class = LoginForm

    def get_success_url(self):
        if self.request.user.is_superuser:
            return reverse_lazy('catalogo:admin_painel')
        return reverse_lazy('catalogo:painel_lojista')

MAX_FOTO_SIZE = 2 * 1024 * 1024


def _parse_decimal(valor):
    if not valor:
        return 0.00
    return float(str(valor).replace(',', '.').replace(' ', ''))


def get_lojista_atual(request):
    lojas = request.user.lojas.all()
    if lojas:
        return lojas[0]
    if request.user.is_superuser:
        return Lojista.objects.first()
    return None

@login_required
def editar_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk, lojista__user=request.user)
    lojista = produto.lojista

    if request.method == 'POST':

        if 'foto' in request.FILES and request.FILES['foto'].size > MAX_FOTO_SIZE:
            messages.error(request, 'A foto principal não pode exceder 2MB.')
            return redirect('catalogo:painel_lojista')

        if 'foto2' in request.FILES and request.FILES['foto2'].size > MAX_FOTO_SIZE:
            messages.error(request, 'A foto secundária não pode exceder 2MB.')
            return redirect('catalogo:painel_lojista')

        produto.nome = request.POST.get('nome')
        produto.preco_base = _parse_decimal(request.POST.get('preco_base'))
        produto.categoria_id = request.POST.get('categoria')
        produto.ativo = request.POST.get('ativo') == 'on'

        if 'foto' in request.FILES:
            if produto.foto:
                produto.foto.delete(save=False)
            produto.foto = request.FILES['foto']

        if 'foto2' in request.FILES:
            if produto.foto2:
                produto.foto2.delete(save=False)
            produto.foto2 = request.FILES['foto2']

        produto.save()

        # Formato do modal: tipo_id[], valor[], preco_adicional[]
        tipo_ids = request.POST.getlist('tipo_id[]')
        if tipo_ids:
            produto.variacoes.all().delete()
            valores = request.POST.getlist('valor[]')
            precos = request.POST.getlist('preco_adicional[]')
            for tipo_id, valor, pa in zip(tipo_ids, valores, precos):
                if valor.strip():
                    tipo = get_object_or_404(TipoVariacao, pk=tipo_id, lojista=lojista)
                    VariacaoProduto.objects.create(
                        produto=produto,
                        tipo=tipo,
                        valor=valor.strip(),
                        preco_adicional=_parse_decimal(pa),
                    )
        else:
            # Formato da página completa: valor_ids[], preco_adicional_<id>
            valor_ids = request.POST.getlist('valor_ids[]')
            if valor_ids:
                produto.variacoes.all().delete()
                for valor_id in valor_ids:
                    valor_obj = get_object_or_404(ValorVariacao, pk=valor_id, tipo__lojista=lojista)
                    pa = _parse_decimal(request.POST.get(f'preco_adicional_{valor_id}', '0.00'))
                    VariacaoProduto.objects.create(
                        produto=produto,
                        tipo=valor_obj.tipo,
                        valor=valor_obj.nome,
                        preco_adicional=pa,
                    )

        messages.success(request, f"Produto '{produto.nome}' atualizado!")
        return redirect('catalogo:painel_lojista')

    tipos_variacao = lojista.tipos_variacao.prefetch_related('valores').all()
    selected_valores = list(produto.variacoes.values_list('valor', flat=True))
    selected_valor_ids = []
    precos_adicionais = {}
    for vp in produto.variacoes.select_related('tipo').all():
        try:
            val = ValorVariacao.objects.get(tipo=vp.tipo, nome=vp.valor)
            selected_valor_ids.append(val.id)
            precos_adicionais[val.id] = vp.preco_adicional
        except ValorVariacao.DoesNotExist:
            pass

    return render(request, 'painel/cadastrar_produto.html', {
        'form': ProdutoForm(instance=produto, lojista=lojista),
        'lojista': lojista,
        'tipos_variacao': tipos_variacao,
        'selected_valores': selected_valor_ids,
        'precos_adicionais': precos_adicionais,
        'editando': produto,
    })


def ver_catalogo(request, slug):
    lojista = get_object_or_404(Lojista, slug=slug)
    if not lojista.ativo:
        return render(request, 'catalogo/loja_desativada.html', {'lojista': lojista})
    categorias = lojista.categorias.prefetch_related('produtos').all()
    produtos = Produto.objects.filter(lojista=lojista, ativo=True).prefetch_related('variacoes__tipo')
    tipos_variacao = lojista.tipos_variacao.all()
    
    context = {
        'lojista': lojista,
        'categorias': categorias,
        'produtos': produtos,
        'tipos_variacao': tipos_variacao,
        'tema': get_tema(lojista.tema),
    }
    return render(request, 'catalogo/app.html', context)


@login_required
def painel_lojista(request):
    lojista = get_lojista_atual(request)

    if not lojista:
        return render(request, 'painel/index.html')

    # Busca os produtos e categorias referentes a este lojista
    produtos = Produto.objects.filter(lojista=lojista)
    categorias = Categoria.objects.filter(lojista=lojista)

    tipos_variacao = lojista.tipos_variacao.all()

    context = {
        'lojista': lojista,
        'produtos': produtos,
        'categorias': categorias,
        'tipos_variacao': tipos_variacao,
    }
    return render(request, 'painel/index.html', context)


@login_required
def cadastrar_produto(request):
    lojista = get_lojista_atual(request)

    if not lojista:
        return redirect('catalogo:painel_lojista')

    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES, lojista=lojista)
        if form.is_valid():
            produto = form.save(commit=False)
            produto.lojista = lojista
            produto.save()

            valor_ids = request.POST.getlist('valor_ids[]')
            for valor_id in valor_ids:
                valor_obj = get_object_or_404(ValorVariacao, pk=valor_id, tipo__lojista=lojista)
                pa_raw = request.POST.get('preco_adicional_' + valor_id, '0.00')
                pa = _parse_decimal(pa_raw)
                VariacaoProduto.objects.create(
                    produto=produto,
                    tipo=valor_obj.tipo,
                    valor=valor_obj.nome,
                    preco_adicional=pa,
                )

            return redirect('catalogo:painel_lojista')
    else:
        form = ProdutoForm(lojista=lojista)

    tipos_variacao = lojista.tipos_variacao.prefetch_related('valores').all()
    return render(request, 'painel/cadastrar_produto.html', {
        'form': form,
        'lojista': lojista,
        'tipos_variacao': tipos_variacao,
        'selected_valores': [],
        'precos_adicionais': {},
        'editando': None,
    })


@login_required
def cadastrar_categoria(request):
    lojista = get_lojista_atual(request)

    if not lojista:
        return redirect('catalogo:painel_lojista')

    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.lojista = lojista
            categoria.save()

            return redirect('catalogo:cadastrar_categoria')
    else:
        form = CategoriaForm()

    categorias_existentes = Categoria.objects.filter(lojista=lojista).order_by('ordem')

    return render(request, 'painel/cadastrar_categoria.html', {
        'form': form,
        'lojista': lojista,
        'categorias': categorias_existentes
    })


@login_required
def configuracoes_lojista(request):
    lojista = get_lojista_atual(request)

    if not lojista:
        return redirect('catalogo:painel_lojista')

    if request.method == 'POST':
        form = ConfiguracaoLojistaForm(request.POST, instance=lojista)
        if form.is_valid():
            form.save()
            return redirect('catalogo:configuracoes_lojista')
    else:
        form = ConfiguracaoLojistaForm(instance=lojista)

    return render(request, 'painel/configuracoes.html', {
        'form': form,
        'lojista': lojista,
        'temas': TEMAS,
    })


@login_required
def gerenciar_variacoes(request):
    lojista = get_lojista_atual(request)

    if not lojista:
        return redirect('catalogo:painel_lojista')

    if request.method == 'POST':
        if 'nome' in request.POST and 'tipo_id' not in request.POST:
            form = TipoVariacaoForm(request.POST)
            if form.is_valid():
                tipo = form.save(commit=False)
                tipo.lojista = lojista
                tipo.save()
                return redirect('catalogo:gerenciar_variacoes')
        elif 'tipo_id' in request.POST and 'valor_nome' in request.POST:
            tipo = get_object_or_404(TipoVariacao, pk=request.POST['tipo_id'], lojista=lojista)
            nome = request.POST.get('valor_nome', '').strip()
            if nome:
                ValorVariacao.objects.get_or_create(tipo=tipo, nome=nome)
            return redirect('catalogo:gerenciar_variacoes')
    else:
        form = TipoVariacaoForm()

    tipos = lojista.tipos_variacao.prefetch_related('valores').all()
    return render(request, 'painel/gerenciar_variacoes.html', {
        'form': form,
        'lojista': lojista,
        'tipos': tipos,
    })


@login_required
def excluir_tipo_variacao(request, pk):
    lojista = get_lojista_atual(request)
    tipo = get_object_or_404(TipoVariacao, pk=pk, lojista=lojista)
    tipo.delete()
    return redirect('catalogo:gerenciar_variacoes')


@login_required
def excluir_valor_variacao(request, pk):
    lojista = get_lojista_atual(request)
    valor = get_object_or_404(ValorVariacao, pk=pk, tipo__lojista=lojista)
    valor.delete()
    return redirect('catalogo:gerenciar_variacoes')


def admin_required(view_func):
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('catalogo:painel_lojista')
        return view_func(request, *args, **kwargs)
    return _wrapped


@admin_required
def admin_painel(request):
    lojistas = Lojista.objects.all().select_related('user')
    total_lojas = lojistas.count()
    total_usuarios = User.objects.filter(is_superuser=False).count()
    total_produtos = Produto.objects.count()
    context = {
        'lojistas': lojistas,
        'total_lojas': total_lojas,
        'total_usuarios': total_usuarios,
        'total_produtos': total_produtos,
    }
    return render(request, 'painel/admin/painel.html', context)


@admin_required
def admin_usuarios(request):
    usuarios = User.objects.all().order_by('username')
    return render(request, 'painel/admin/usuarios.html', {
        'usuarios': usuarios,
    })


@admin_required
def admin_usuario_novo(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        if username and senha:
            user = User.objects.create_user(username=username, email=email, password=senha)
            messages.success(request, f'Usuário "{username}" criado!')
            return redirect('catalogo:admin_usuarios')
        else:
            messages.error(request, 'Usuário e senha são obrigatórios.')
    return render(request, 'painel/admin/usuario_form.html')


@admin_required
def admin_usuario_desativar(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        messages.error(request, 'Não é possível desativar o administrador.')
        return redirect('catalogo:admin_usuarios')
    user.is_active = not user.is_active
    user.save()
    status = 'ativado' if user.is_active else 'desativado'
    messages.success(request, f'Usuário "{user.username}" {status}!')
    return redirect('catalogo:admin_usuarios')


@admin_required
def admin_loja_nova(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        nome_loja = request.POST.get('nome_loja')
        whatsapp = request.POST.get('whatsapp')
        tema = request.POST.get('tema', 'minimal_nordic')

        if not all([user_id, nome_loja]):
            messages.error(request, 'Usuário e nome da loja são obrigatórios.')
        else:
            user = get_object_or_404(User, pk=user_id)
            lojista = Lojista.objects.create(
                user=user,
                nome_loja=nome_loja,
                slug=slug_unico(slugify(nome_loja)),
                whatsapp=whatsapp or '',
                tema=tema,
            )

            categorias_nomes = request.POST.getlist('categoria_nome[]')
            for nome in categorias_nomes:
                if nome.strip():
                    Categoria.objects.create(lojista=lojista, nome=nome.strip())

            tipos_nomes = request.POST.getlist('tipo_nome[]')
            for nome in tipos_nomes:
                if nome.strip():
                    TipoVariacao.objects.get_or_create(lojista=lojista, nome=nome.strip())

            messages.success(request, f'Loja "{nome_loja}" criada!')
            return redirect('catalogo:admin_painel')

    usuarios = User.objects.all().order_by('username')
    return render(request, 'painel/admin/loja_form.html', {
        'usuarios': usuarios,
        'temas': Lojista.TEMAS_CHOICES,
    })


@admin_required
def admin_loja_editar(request, pk):
    lojista = get_object_or_404(Lojista, pk=pk)

    if request.method == 'POST':
        lojista.nome_loja = request.POST.get('nome_loja')
        lojista.slug = slug_unico(slugify(lojista.nome_loja), instance=lojista)
        lojista.whatsapp = request.POST.get('whatsapp', '')
        lojista.tema = request.POST.get('tema', 'minimal_nordic')
        lojista.user_id = request.POST.get('user_id')
        lojista.save()

        lojista.categorias.all().delete()
        for nome in request.POST.getlist('categoria_nome[]'):
            if nome.strip():
                Categoria.objects.create(lojista=lojista, nome=nome.strip())

        lojista.tipos_variacao.all().delete()
        for nome in request.POST.getlist('tipo_nome[]'):
            if nome.strip():
                TipoVariacao.objects.create(lojista=lojista, nome=nome.strip())

        messages.success(request, f'Loja "{lojista.nome_loja}" atualizada!')
        return redirect('catalogo:admin_painel')

    usuarios = User.objects.all().order_by('username')
    return render(request, 'painel/admin/loja_form.html', {
        'lojista': lojista,
        'usuarios': usuarios,
        'temas': Lojista.TEMAS_CHOICES,
    })


@admin_required
def admin_loja_desativar(request, pk):
    lojista = get_object_or_404(Lojista, pk=pk)
    lojista.ativo = not lojista.ativo
    lojista.save()
    status = 'ativada' if lojista.ativo else 'desativada'
    messages.success(request, f'Loja "{lojista.nome_loja}" {status}!')
    return redirect('catalogo:admin_painel')


@admin_required
def admin_loja_excluir(request, pk):
    lojista = get_object_or_404(Lojista, pk=pk)
    if lojista.ativo:
        messages.error(request, f'Desative a loja "{lojista.nome_loja}" antes de excluí-la.')
        return redirect('catalogo:admin_painel')
    nome = lojista.nome_loja
    lojista.delete()
    messages.success(request, f'Loja "{nome}" excluída!')
    return redirect('catalogo:admin_painel')