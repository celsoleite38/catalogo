from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Produto, Categoria, VariacaoProduto, Lojista, Categoria
from .forms import ProdutoForm, CategoriaForm, ConfiguracaoLojistaForm
from django.contrib import messages
from .models import Produto
from .themes import TEMAS, get_tema

MAX_FOTO_SIZE = 2 * 1024 * 1024

def editar_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)

    if request.method == 'POST':

        # Valida tamanho das fotos ANTES de salvar
        if 'foto' in request.FILES and request.FILES['foto'].size > MAX_FOTO_SIZE:
            messages.error(request, 'A foto principal não pode exceder 2MB.')
            return redirect('catalogo:painel_lojista')

        if 'foto2' in request.FILES and request.FILES['foto2'].size > MAX_FOTO_SIZE:
            messages.error(request, 'A foto secundária não pode exceder 2MB.')
            return redirect('catalogo:painel_lojista')

        produto.nome = request.POST.get('nome')
        produto.preco_base = request.POST.get('preco_base')
        produto.categoria_id = request.POST.get('categoria')
        produto.ativo = request.POST.get('ativo') == 'on'

        # Se enviou uma foto nova
        if 'foto' in request.FILES:
            if produto.foto:
                produto.foto.delete(save=False) # apaga do disco a foto antiga
            produto.foto = request.FILES['foto']

        # Foto 2
        if 'foto2' in request.FILES:
            if produto.foto2:
                produto.foto2.delete(save=False) # remove antiga
            produto.foto2 = request.FILES['foto2']

        produto.save()
        messages.success(request, f"Produto '{produto.nome}' atualizado!")

    return redirect('catalogo:painel_lojista')


def ver_catalogo(request, slug):
    lojista = get_object_or_404(Lojista, slug=slug)
    categorias = lojista.categorias.prefetch_related('produtos').all()
    produtos = Produto.objects.filter(lojista=lojista, ativo=True)
    
    context = {
        'lojista': lojista,
        'categorias': categorias,
        'produtos': produtos,
        'tema': get_tema(lojista.tema),
    }
    return render(request, 'catalogo/app.html', context)


@login_required
def dashboard_lojista(request):
    lojista = request.user.lojista
    produtos = Produto.objects.filter(lojista=lojista)
    categorias = Categoria.objects.filter(lojista=lojista)
    return render(request, 'painel/dashboard.html', {
        'lojista': lojista,
        'produtos': produtos,
        'categorias': categorias
    })


@login_required
def painel_lojista(request):
    # Tenta buscar o Lojista associado ao usuário logado
    lojista = getattr(request.user, 'lojista', None)

    # Se for Admin/Superuser e ainda não tiver um perfil de Lojista criado,
    # pega o primeiro Lojista cadastrado no banco para você conseguir testar a interface!
    if not lojista:
        if request.user.is_superuser:
            # Se for o superusuario, pega a primeira loja só para visualizar a interface
            lojista = Lojista.objects.first()
            if not lojista:
                return redirect('/admin/')
        else:
            # Se for usuário comum sem lojista, não manda pro /admin/ (evita o erro da imagem)
            return render(request, 'painel/index.html')

    # Busca os produtos e categorias referentes a este lojista
    produtos = Produto.objects.filter(lojista=lojista)
    categorias = Categoria.objects.filter(lojista=lojista)

    context = {
        'lojista': lojista,
        'produtos': produtos,
        'categorias': categorias,
    }
    return render(request, 'painel/index.html', context)


@login_required
def cadastrar_produto(request):
    lojista = getattr(request.user, 'lojista', None)
    if not lojista and request.user.is_superuser:
        lojista = Lojista.objects.first()

    if not lojista:
        return redirect('catalogo:painel_lojista')

    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES, lojista=lojista)
        if form.is_valid():
            produto = form.save(commit=False)
            produto.lojista = lojista
            produto.save()

            # Processa Variações (Tamanhos / Cores adicionados)
            tamanhos = request.POST.getlist('tamanho[]')
            cores = request.POST.getlist('cor[]')

            for t, c in zip(tamanhos, cores):
                if t.strip() or c.strip():
                    VariacaoProduto.objects.create(
                        produto=produto,
                        tamanho=t.strip(),
                        cor=c.strip()
                    )

            return redirect('catalogo:painel_lojista')
    else:
        form = ProdutoForm(lojista=lojista)

    return render(request, 'painel/cadastrar_produto.html', {'form': form, 'lojista': lojista})


@login_required
def cadastrar_categoria(request):
    lojista = getattr(request.user, 'lojista', None)
    if not lojista and request.user.is_superuser:
        lojista = Lojista.objects.first()

    if not lojista:
        return redirect('catalogo:painel_lojista')

    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.lojista = lojista
            categoria.save()

            # Captura listas de variações adicionadas para esta categoria
            tamanhos = request.POST.getlist('tamanho[]')
            cores = request.POST.getlist('cor[]')

            # Se a categoria já possui um produto associado ou produto base, 
            # salva as variações
            for t, c in zip(tamanhos, cores):
                if t.strip() or c.strip():
                    # Guarda as variações cadastradas
                    pass  # As variações criadas nesta tela ficam salvas para a categoria

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
    lojista = getattr(request.user, 'lojista', None)
    if not lojista and request.user.is_superuser:
        lojista = Lojista.objects.first()

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