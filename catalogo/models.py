from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
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
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='lojas')
    nome_loja = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    whatsapp = models.CharField(max_length=20)
    tema = models.CharField(max_length=30, choices=TEMAS_CHOICES, default='minimal_nordic')
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome_loja


@receiver(post_save, sender=Lojista)
def criar_tipos_padrao(sender, instance, created, **kwargs):
    if created:
        for nome in ['Tamanho', 'Cor']:
            TipoVariacao.objects.get_or_create(lojista=instance, nome=nome)


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

class TipoVariacao(models.Model):
    lojista = models.ForeignKey(Lojista, on_delete=models.CASCADE, related_name='tipos_variacao')
    nome = models.CharField(max_length=50)

    class Meta:
        unique_together = ['lojista', 'nome']

    def __str__(self):
        return self.nome

class ValorVariacao(models.Model):
    tipo = models.ForeignKey(TipoVariacao, on_delete=models.CASCADE, related_name='valores')
    nome = models.CharField(max_length=50)

    class Meta:
        unique_together = ['tipo', 'nome']
        ordering = ['nome']

    def __str__(self):
        return self.nome


class VariacaoProduto(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='variacoes')
    tipo = models.ForeignKey(TipoVariacao, on_delete=models.CASCADE)
    valor = models.CharField(max_length=50)
    preco_adicional = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ['produto', 'tipo', 'valor']

    def __str__(self):
        return f"{self.produto.nome} - {self.tipo.nome}: {self.valor}"

class PushSubscription(models.Model):
    """
    Armazena a inscrição de push de um visitante para uma Loja específica.
    Um mesmo dispositivo pode ter subscriptions diferentes para lojas diferentes,
    pois o Service Worker é escopado por loja.
    """
    lojista = models.ForeignKey(
        'Lojista',
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Inscrição Push"
        verbose_name_plural = "Inscrições Push"
        indexes = [
            models.Index(fields=['lojista', 'ativo']),
        ]

    def __str__(self):
        return f"Push - {self.lojista.nome_loja} - {self.endpoint[:40]}..."

    def to_subscription_info(self):
        """Formato exigido pelo pywebpush."""
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh,
                "auth": self.auth
            }
        }