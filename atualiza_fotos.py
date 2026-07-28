import os
import django
import requests
from django.core.files.base import ContentFile

# Configuração do ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from catalogo.models import Produto

# Mapeamento de palavras-chave para URLs fixas de alta qualidade no Unsplash
MAPA_IMAGENS = {
    "camiseta": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&q=80",
    "shirt": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&q=80",
    "tenis": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=800&q=80",
    "tênis": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=800&q=80",
    "sapato": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=800&q=80",
    "bone": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=800&q=80",
    "boné": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=800&q=80",
    "jaqueta": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=800&q=80",
    "casaco": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=800&q=80",
    "oculos": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=800&q=80",
    "óculos": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=800&q=80",
    "mochila": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80",
    "bolsa": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80",
    "calca": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=800&q=80",
    "calça": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=800&q=80",
    "relogio": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80",
    "relógio": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80",
}

# Fallback genérico caso o nome do produto não bata com nenhuma palavra-chave
URL_PADRAO = "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80"


def obter_url_por_nome(nome_produto):
    nome_lc = nome_produto.lower()
    for palavra, url in MAPA_IMAGENS.items():
        if palavra in nome_lc:
            return url
    return URL_PADRAO


def baixar_imagem(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return ContentFile(response.content)
    except Exception as e:
        print(f"  ❌ Erro ao baixar ({url}): {e}")
    return None


def forcar_atualizacao_fotos():
    produtos = Produto.objects.all()

    if not produtos.exists():
        print("❌ Nenhum produto encontrado no banco de dados!")
        return

    print(f"📦 Recarregando fotos de {produtos.count()} produto(s)...\n")

    for produto in produtos:
        print(f"🔍 Produto ID {produto.id}: '{produto.nome}'")

        # 1. Remove o arquivo antigo associado do banco/disco se existir
        if produto.foto:
            produto.foto.delete(save=False)

        url_foto = obter_url_por_nome(produto.nome)
        print(f"   🖼️ Baixando nova imagem contextual...")

        imagem_content = baixar_imagem(url_foto)

        if imagem_content:
            nome_limpo = "".join([c if c.isalnum() else "_" for c in produto.nome.lower()])
            nome_arquivo = f"prod_{produto.id}_{nome_limpo}.jpg"

            # 2. Salva explicitamente a nova foto
            produto.foto.save(nome_arquivo, imagem_content, save=True)
            print(f"   ✅ Foto atualizada com sucesso!\n")
        else:
            print(f"   ⚠️ Falha ao baixar imagem para este produto.\n")

    print("🎉 Fotos atualizadas com sucesso!")


if __name__ == "__main__":
    forcar_atualizacao_fotos()