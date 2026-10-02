from django.db import models


class Plano(models.Model):
    """Plano de assinatura do catálogo, sincronizado com a Central de Cobranças."""

    CICLO_CHOICES = [
        ('WEEKLY', 'Semanal'),
        ('MONTHLY', 'Mensal'),
        ('BIMONTHLY', 'Bimestral'),
        ('QUARTERLY', 'Trimestral'),
        ('SEMIANNUALLY', 'Semestral'),
        ('YEARLY', 'Anual'),
    ]

    codigo = models.SlugField(max_length=50, unique=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    ciclo = models.CharField(max_length=20, choices=CICLO_CHOICES, default='MONTHLY')
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'valor']
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'

    def __str__(self):
        return f'{self.nome} - R$ {self.valor}'


class ConfiguracaoGlobal(models.Model):
    """Configurações globais do sistema (uma única linha no banco).

    Contém o período de trial único do catálogo, valendo para todos os
    planos e todos os novos cadastros. Editável pelo admin.
    """

    dias_trial = models.IntegerField(
        default=30,
        help_text='Dias de trial global. 0 = sem trial.',
    )

    class Meta:
        verbose_name = 'Configuração Global'
        verbose_name_plural = 'Configurações Globais'

    def __str__(self):
        return f'Configuração Global (trial: {self.dias_trial} dias)'