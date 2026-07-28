from django.db import models
from django.contrib.auth.models import User
import os
from django.utils.text import slugify

class Lojista(models.Model):
    TEMAS_CHOICES = [
        ('modern_emerald', 'Emerald Clean (Verde & Padrão)'),
        ('dark_neon', 'Dark Premium (Escuro & Neon)'),
        ('warm_sunset', 'Warm Sunset (Laranja & Gourmet)'),
        ('minimal_nordic', 'Minimal Nordic (Cinza & Elegante)'),
        ('vibrant_purple', 'Vibrant Tech (Roxo & Moderno)'),
        ('candy_pastels', 'Candy Pastels (Rosa & Suave)'),
        ('rustic_earth', 'Rustic Earth (Café & Artesanal)'),
        ('sport_fire', 'Sport Fire (Preto & Vermelho)'),
        ('ocean_breeze', 'Ocean Breeze (Azul & Frescor)'),
        ('luxury_gold', 'Luxury Gold (Preto & Dourado)'),
        ('cyber_punk', 'Cyber Punk (Roxo & Magenta Neon)'),
        ('sunset_drive', 'Sunset Drive (Laranja & Coral)'),
        ('mint_fresh', 'Mint Fresh (Menta & Saúde)'),
        ('vintage_craft', 'Vintage Craft (Vinho & Retrô)'),
        ('royal_blue', 'Royal Blue (Azul & Corporativo)'),
    ]
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    nome_loja = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    whatsapp = models.CharField(max_length=20)
    tema = models.CharField(max_length=30, choices=TEMAS_CHOICES, default='minimal_nordic')

    def __str__(self):
        return self.nome_loja


class Categoria(models.Model):
    lojista = models.ForeignKey(Lojista, on_delete=models.CASCADE, related_name='categorias')
    nome = models.CharField(max_length=50)
    ordem = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'nome']

    def __str__(self):
        return f"{self.nome} - {self.lojista.nome_loja}"

def caminho_foto_produto(instance, filename):
    
    # Tenta pegar o nome da loja via relacionamento
    if hasattr(instance, 'lojista') and instance.lojista:
        loja_slug = slugify(instance.lojista.nome_loja)
    elif hasattr(instance, 'categoria') and instance.categoria and instance.categoria.lojista:
        loja_slug = slugify(instance.categoria.lojista.nome_loja)
    else:
        loja_slug = "geral"

    # Retorna o caminho relativo dentro da pasta MEDIA_ROOT
    return os.path.join('produtos', loja_slug, filename)

class Produto(models.Model):
    lojista = models.ForeignKey(Lojista, on_delete=models.CASCADE, related_name='produtos')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='produtos')
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    preco_base = models.DecimalField(max_digits=8, decimal_places=2)
    foto = models.ImageField(upload_to=caminho_foto_produto, blank=True, null=True)
    foto2 = models.ImageField(upload_to=caminho_foto_produto, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class VariacaoProduto(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='variacoes')
    tamanho = models.CharField(max_length=20, blank=True, help_text="Ex: P, M, G, 42")
    cor = models.CharField(max_length=30, blank=True, help_text="Ex: Azul, Preto")
    preco_adicional = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="Valor extra caso mude o preço")

    def __str__(self):
        variacao = []
        if self.tamanho: variacao.append(f"Tamanho: {self.tamanho}")
        if self.cor: variacao.append(f"Cor: {self.cor}")
        return f"{self.produto.nome} ({', '.join(variacao)})"




