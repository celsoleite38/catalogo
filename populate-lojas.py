import os
import django
import requests
from django.core.files.base import ContentFile

# Inicializa as configurações do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')  # Ajuste 'core' se o nome da pasta do seu settings for diferente
django.setup()

# Importe dos models (garanta que Variacao esteja importado)
from catalogo.models import Lojista, Categoria, Produto #Variacao


def baixar_imagem(url):
    """Auxiliar para baixar uma imagem via HTTP e retornar como ContentFile."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return ContentFile(response.content)
    except Exception as e:
        print(f"⚠️ Erro ao baixar imagem da URL ({url}): {e}")
    return None


def popular_banco():
    print("🚀 Iniciando o populate do catálogo...")

    # 1. Lojista de Exemplo
    lojista, _ = Lojista.objects.get_or_create(
        whatsapp="5535999998888",
        defaults={
            "nome_loja": "Urban & Style Co.",
            "tema": "modern_emerald"
        }
    )
    print(f"✅ Lojista configurado: {lojista.nome_loja}")

    # 2. Categorias
    cat_camisetas, _ = Categoria.objects.get_or_create(nome="Camisetas", lojista=lojista)
    cat_calcados, _ = Categoria.objects.get_or_create(nome="Calçados", lojista=lojista)
    cat_acessorios, _ = Categoria.objects.get_or_create(nome="Acessórios", lojista=lojista)

    # 3. Estrutura de Produtos, Imagens e Variações
    produtos_dados = [
        {
            "nome": "Camiseta Oversized Minimalist",
            "descricao": "Camiseta 100% algodão egípcio com corte oversized moderno e caimento impecável.",
            "preco_base": 129.90,
            "categoria": cat_camisetas,
            "foto_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&q=80",
            "variacoes": [
                {"tamanho": "P", "cor": "Preto"},
                {"tamanho": "M", "cor": "Preto"},
                {"tamanho": "G", "cor": "Preto"},
                {"tamanho": "M", "cor": "Branco"},
                {"tamanho": "G", "cor": "Branco"},
            ]
        },
        {
            "nome": "Tênis Streetwear White Minimal",
            "descricao": "Tênis urbano em couro legítimo, solado reto vulcanizado e máximo conforto.",
            "preco_base": 349.00,
            "categoria": cat_calcados,
            "foto_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=800&q=80",
            "variacoes": [
                {"tamanho": "38", "cor": "Branco"},
                {"tamanho": "39", "cor": "Branco"},
                {"tamanho": "40", "cor": "Branco"},
                {"tamanho": "41", "cor": "Branco"},
                {"tamanho": "42", "cor": "Off-White"},
            ]
        },
        {
            "nome": "Boné Aba Curva Premium",
            "descricao": "Boné aba curva com ajuste de fivela metálica e tecido sarja resinado.",
            "preco_base": 89.90,
            "categoria": cat_acessorios,
            "foto_url": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=800&q=80",
            "variacoes": [
                {"tamanho": "Único", "cor": "Preto"},
                {"tamanho": "Único", "cor": "Bege"},
                {"tamanho": "Único", "cor": "Verde Militar"},
            ]
        },
        {
            "nome": "Jaqueta Jeans Vintage Wash",
            "descricao": "Jaqueta jeans com lavagem clássica estilo anos 90, botões em latão e reforço duplo.",
            "preco_base": 279.90,
            "categoria": cat_camisetas,
            "foto_url": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=800&q=80",
            "variacoes": [
                {"tamanho": "M", "cor": "Jeans Claro"},
                {"tamanho": "G", "cor": "Jeans Claro"},
                {"tamanho": "GG", "cor": "Jeans Escuro"},
            ]
        },
        {
            "nome": "Óculos de Sol Retro Oval",
            "descricao": "Armação em acetato italiano com proteção UV400 total contra raios solares.",
            "preco_base": 159.00,
            "categoria": cat_acessorios,
            "foto_url": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=800&q=80",
            "variacoes": [
                {"tamanho": "Único", "cor": "Tartaruga"},
                {"tamanho": "Único", "cor": "Preto Fosco"},
            ]
        },
        {
            "nome": "Mochila Urbana Roll-Top",
            "descricao": "Mochila impermeável com compartimento acolchoado para notebook de até 15.6 polegadas.",
            "preco_base": 219.90,
            "categoria": cat_acessorios,
            "foto_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80",
            "variacoes": [
                {"tamanho": "Único", "cor": "Cinza Chumbo"},
                {"tamanho": "Único", "cor": "Preto"},
            ]
        },
    ]

    for p_data in produtos_dados:
        produto, criado = Produto.objects.get_or_create(
            nome=p_data["nome"],
            defaults={
                "descricao": p_data["descricao"],
                "preco_base": p_data["preco_base"],
                "categoria": p_data["categoria"],
            }
        )

        # Baixa a foto caso o produto acabou de ser criado ou se ainda não tiver imagem associada
        if criado or not produto.foto:
            print(f"🖼️ Baixando imagem para: {produto.nome}...")
            imagem_content = baixar_imagem(p_data["foto_url"])
            if imagem_content:
                nome_arquivo = f"{produto.nome.lower().replace(' ', '_').replace('/', '_')}.jpg"
                produto.foto.save(nome_arquivo, imagem_content, save=True)

        # Cadastra as variações
        for v_data in p_data["variacoes"]:
            Variacao.objects.get_or_create(
                produto=produto,
                tamanho=v_data.get("tamanho"),
                cor=v_data.get("cor")
            )

        print(f"✨ Produto '{produto.nome}' atualizado com imagem e {len(p_data['variacoes'])} variações!")

    print("\n✅ Povoamento do catálogo concluído com sucesso!")


if __name__ == "__main__":
    popular_banco()