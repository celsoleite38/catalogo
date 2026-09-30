"""Avisos automáticos do trial por e-mail + pausa da vitrine pública.

Executar 1x por dia (cron):

    0 9 * * *  cd /var/www/catalogo && venv/bin/python manage.py enviar_avisos_trial
"""
from datetime import date, timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.urls import reverse

from catalogo.models import Lojista, TrialAviso

DIAS_ANTES = [5, 3, 1]
DIAS_DEPOIS = [1, 3, 5, 7, 10]


class Command(BaseCommand):
    help = 'Envia os avisos do trial (5/3/1 dias antes e 1/3/5/7/10 dias depois) e pausa a vitrine vencida.'

    def handle(self, *args, **options):
        hoje = date.today()
        site = (getattr(settings, 'SITE_URL', '') or '').rstrip('/')
        if not site:
            self.stdout.write(self.style.WARNING(
                'SITE_URL não configurado: os e-mails sairão sem link. '
                'Defina SITE_URL no .env com o domínio público do catálogo.'
            ))

        enviados = 0
        pausadas = 0

        for lojista in Lojista.objects.filter(status_assinatura='trial').exclude(trial_fim=None):
            if lojista.trial_fim < hoje and lojista.ativo:
                # Vitrine pública pausa quando o trial vence.
                Lojista.objects.filter(pk=lojista.pk).update(ativo=False)
                pausadas += 1

            for dias in DIAS_ANTES:
                if lojista.trial_fim == hoje + timedelta(days=dias):
                    enviados += self._envia(lojista, 'antes', dias, site)

            if lojista.status_assinatura != 'ativa':
                for dias in DIAS_DEPOIS:
                    if lojista.trial_fim == hoje - timedelta(days=dias):
                        enviados += self._envia(lojista, 'depois', dias, site)

        self.stdout.write(self.style.SUCCESS(
            f'{enviados} e-mail(s) enviado(s) e {pausadas} vitrine(s) pausada(s).'
        ))

    def _envia(self, lojista, momento, dias, site):
        _, criado = TrialAviso.objects.get_or_create(
            lojista=lojista, momento=momento, dias=dias
        )
        if not criado:
            return 0

        email = getattr(lojista.user, 'email', '')
        if not email:
            return 0

        contexto = {
            'lojista': lojista,
            'momento': momento,
            'dias': dias,
            'trial_fim': lojista.trial_fim,
            'planos_url': f"{site}{reverse('planos:pagina_planos')}" if site else '',
        }
        assunto = render_to_string('planos/email_trial_assunto.txt', contexto).strip()
        corpo = render_to_string('planos/email_trial_corpo.txt', contexto)

        mensagem = EmailMultiAlternatives(
            assunto,
            corpo,
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )
        mensagem.send(fail_silently=False)
        self.stdout.write(f'  e-mail {momento} D{dias:+d} -> {email}')
        return 1
