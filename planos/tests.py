from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase, RequestFactory, override_settings

from catalogo.models import Lojista, TrialAviso
from planos.models import Plano
from planos.services import trial as trial_service
from planos.services import central_client
from planos.templatetags.planos_tags import aviso_trial

User = get_user_model()

PNG_1PX = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06'
    b'\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05'
    b'\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)

SEM_ACESSO = {'pode_acessar': False, 'status': 'sem_assinatura'}
COM_TRIAL = {'pode_acessar': True, 'status': 'trial'}
COM_PAGAMENTO = {'pode_acessar': True, 'status': 'ativa'}


@override_settings(MEDIA_ROOT='/tmp/opencode/test-media-trial')
class TrialTests(TestCase):
    def setUp(self):
        cfg = trial_service.get_config()
        cfg.dias_trial = 3
        cfg.save()
        self.plano = Plano.objects.create(
            codigo='teste', nome='Teste', valor=10, ciclo='MONTHLY',
            ativo=True, ordem=1,
        )
        self.user = User.objects.create_user('t1', 't1@x.com', 'x')
        self.lojista = Lojista.objects.create(
            user=self.user, nome_loja='Loja 1', slug='loja-1', whatsapp='1',
            cnpj='00000000000199',
            logo=SimpleUploadedFile('logo.png', PNG_1PX, content_type='image/png'),
            status_assinatura='trial', trial_fim=date.today() + timedelta(days=3),
            ativo=True,
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.rf = RequestFactory()

    def banner(self):
        request = self.rf.get('/')
        request.user = self.user
        return aviso_trial({'request': request})

    def aponta_para_planos(self, resp):
        return resp.status_code == 302 and '/planos/' in resp.get('Location', '')

    # --- regras do trial global ---
    def test_dias_vem_da_configuracao_global(self):
        self.assertEqual(trial_service.dias_trial(), 3)
        self.assertEqual(trial_service.data_fim_trial(), date.today() + timedelta(days=3))

    def test_zero_significa_sem_trial(self):
        cfg = trial_service.get_config()
        cfg.dias_trial = 0
        cfg.save()
        self.assertEqual(trial_service.dias_trial(), 0)
        self.assertIsNone(trial_service.data_fim_trial())

    def test_plano_mais_barato_e_a_referencia(self):
        Plano.objects.create(codigo='caro', nome='Caro', valor=99, ativo=True, ordem=2)
        self.assertEqual(trial_service.plano_referencia().codigo, 'teste')

    def test_planos_listam_o_mesmo_trial_global(self):
        planos = central_client.listar_planos()
        dias = {p['dias_trial'] for p in planos}
        self.assertEqual(dias, {3})

    # --- banner D-5..D-1 ---
    def test_banner_aparece_ate_d1(self):
        self.assertTrue(self.banner()['mostrar'])
        self.assertEqual(self.banner()['dias'], 3)

    def test_banner_some_no_d6(self):
        self.lojista.trial_fim = date.today() + timedelta(days=6)
        self.lojista.save()
        self.assertFalse(self.banner()['mostrar'])

    def test_banner_some_apos_vencer(self):
        self.lojista.trial_fim = date.today() - timedelta(days=1)
        self.lojista.save()
        self.assertFalse(self.banner()['mostrar'])

    def test_banner_ausente_quando_pago(self):
        self.lojista.status_assinatura = 'ativa'
        self.lojista.save()
        self.assertFalse(self.banner()['mostrar'])

    # --- trava do painel ---
    @patch('planos.services.central_client.verificar_acesso', return_value=SEM_ACESSO)
    def test_painel_liberado_no_trial(self, _m):
        for url in ['/painel/', '/painel/configuracoes/',
                    '/painel/produtos/novo/', '/painel/categorias/nova/',
                    '/painel/variacoes/']:
            resp = self.client.get(url)
            self.assertNotEqual(resp.status_code, 302, f'{url} foi bloqueado no trial')

    @patch('planos.services.central_client.verificar_acesso', return_value=SEM_ACESSO)
    def test_painel_bloqueado_depois_do_vencimento(self, _m):
        self.lojista.trial_fim = date.today() - timedelta(days=1)
        self.lojista.save()
        for url in ['/painel/', '/painel/configuracoes/',
                    '/painel/produtos/novo/', '/painel/categorias/nova/',
                    '/painel/variacoes/']:
            self.assertTrue(self.aponta_para_planos(self.client.get(url)), url)

    @patch('planos.services.central_client.verificar_acesso', return_value=SEM_ACESSO)
    def test_painel_bloqueado_sem_trial(self, _m):
        """dias_trial = 0: loja sem assinatura vai direto para o pagamento."""
        self.lojista.status_assinatura = 'inativa'
        self.lojista.trial_fim = None
        self.lojista.ativo = False
        self.lojista.save()
        r = self.client.get('/painel/')
        self.assertTrue(self.aponta_para_planos(r), f'{r.status_code} -> {r.get("Location")}')

    @patch('planos.services.central_client.verificar_acesso', return_value=SEM_ACESSO)
    def test_inativa_com_trial_futuro_libera_painel(self, _m):
        """Status 'inativa' + validade futura já caracteriza trial válido."""
        self.lojista.status_assinatura = 'inativa'
        self.lojista.trial_fim = date.today() + timedelta(days=3)
        self.lojista.save()
        resp = self.client.get('/painel/')
        self.assertNotEqual(resp.status_code, 302, 'painel foi bloqueado no trial')

    @patch('planos.services.central_client.verificar_acesso', return_value=SEM_ACESSO)
    def test_cancelada_com_trial_futuro_vai_para_planos(self, _m):
        """Cancelado não herda acesso por um trial_fim remanescente."""
        self.lojista.status_assinatura = 'cancelada'
        self.lojista.trial_fim = date.today() + timedelta(days=3)
        self.lojista.save()
        r = self.client.get('/painel/')
        self.assertTrue(self.aponta_para_planos(r), f'{r.status_code} -> {r.get("Location")}')

    @patch('planos.services.central_client.verificar_acesso', return_value=COM_TRIAL)
    def test_central_manda_trial_libera_painel(self, _m):
        self.lojista.status_assinatura = 'inativa'
        self.lojista.trial_fim = None
        self.lojista.save()
        self.assertNotEqual(self.client.get('/painel/').status_code, 302)

    @patch('planos.services.central_client.verificar_acesso', return_value=COM_TRIAL)
    def test_painel_liberto_mostra_banner_offline(self, _m):
        self.lojista.ativo = False
        self.lojista.trial_fim = date.today() - timedelta(days=1)
        self.lojista.save()
        resp = self.client.get('/painel/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'vitrine está offline')
        self.assertContains(resp, 'Ver planos')

    # --- fluxo de cadastro (não pode cair em /planos/ sem ter loja) ---
    def test_cadastro_para_autenticado_leva_ao_perfil(self):
        resp = self.client.get('/usuarios/cadastro/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/usuarios/perfil/', resp['Location'])

    @patch('planos.services.central_client.verificar_acesso', return_value=SEM_ACESSO)
    def test_usuario_sem_loja_nao_cai_em_planos(self, _m):
        user_sem_loja = User.objects.create_user('t2', 't2@x.com', 'x')
        self.client.force_login(user_sem_loja)
        resp = self.client.get('/painel/')
        self.assertFalse(self.aponta_para_planos(resp), f'{resp.status_code} -> {resp.get("Location")}')

    # --- vitrine pública ---
    def test_vitrine_online_no_trial(self):
        self.assertEqual(self.client.get('/loja-1/').status_code, 200)

    def test_vitrine_bloqueada_trial_vencido_sem_cron(self):
        self.lojista.trial_fim = date.today() - timedelta(days=1)
        self.lojista.save()
        resp = self.client.get('/loja-1/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'fora do ar')

    def test_vitrine_bloqueada_inativa_sem_trial(self):
        self.lojista.status_assinatura = 'inativa'
        self.lojista.trial_fim = None
        self.lojista.save()
        self.assertContains(self.client.get('/loja-1/'), 'fora do ar')

    def test_vitrine_bloqueada_cancelada_com_trial_futuro(self):
        self.lojista.status_assinatura = 'cancelada'
        self.lojista.trial_fim = date.today() + timedelta(days=3)
        self.lojista.save()
        self.assertContains(self.client.get('/loja-1/'), 'fora do ar')

    def test_vitrine_aberta_inativa_com_validade_futura(self):
        self.lojista.status_assinatura = 'inativa'
        self.lojista.trial_fim = date.today() + timedelta(days=3)
        self.lojista.save()
        resp = self.client.get('/loja-1/')
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'fora do ar')

    def test_manifest_liberado_no_trial(self):
        self.assertEqual(self.client.get('/loja-1/manifest.json').status_code, 200)

    def test_manifest_bloqueado_sem_acesso(self):
        self.lojista.status_assinatura = 'inativa'
        self.lojista.trial_fim = None
        self.lojista.save()
        self.assertEqual(self.client.get('/loja-1/manifest.json').status_code, 404)

    @patch('planos.services.central_client.verificar_acesso', return_value=SEM_ACESSO)
    def test_comando_pausa_vitrine_vencida(self, _m):
        self.lojista.trial_fim = date.today() - timedelta(days=1)
        self.lojista.save()
        call_command('enviar_avisos_trial')
        self.lojista.refresh_from_db()
        self.assertFalse(self.lojista.ativo)
        resp = self.client.get('/loja-1/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'fora do ar')

    def test_webhook_pagamento_reativa_loja(self):
        self.lojista.trial_fim = date.today() - timedelta(days=1)
        self.lojista.ativo = False
        self.lojista.save()
        resp = self.client.post(
            '/planos/webhook/central/',
            data={'assinatura': {'email': 't1@x.com', 'status': 'ativa',
                                 'proximo_vencimento': str(date.today() + timedelta(days=30))}},
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.lojista.refresh_from_db()
        self.assertTrue(self.lojista.ativo)
        self.assertEqual(self.lojista.status_assinatura, 'ativa')

    @patch('planos.services.central_client.verificar_acesso', return_value=COM_PAGAMENTO)
    def test_pagamento_confirmado_reativa_vitrine_no_acesso(self, _m):
        """A Central não avisa o catálogo, então é o painel que sincroniza."""
        self.lojista.status_assinatura = 'inativa'
        self.lojista.trial_fim = None
        self.lojista.ativo = False
        self.lojista.save()

        resp = self.client.get('/painel/')
        self.assertEqual(resp.status_code, 200)

        self.lojista.refresh_from_db()
        self.assertEqual(self.lojista.status_assinatura, 'ativa')
        self.assertIsNone(self.lojista.trial_fim)
        self.assertTrue(self.lojista.ativo)
        vitrine = self.client.get('/loja-1/')
        self.assertEqual(vitrine.status_code, 200)
        self.assertNotContains(vitrine, 'fora do ar')

    # --- e-mails ---
    def _roda_comando(self):
        call_command('enviar_avisos_trial')

    def _limpa_caixa(self):
        mail.outbox.clear()

    def test_email_antes_d5(self):
        self.lojista.trial_fim = date.today() + timedelta(days=5)
        self.lojista.save()
        self._roda_comando()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('5 dias', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ['t1@x.com'])

    def test_email_antes_d1_diz_amanha(self):
        self.lojista.trial_fim = date.today() + timedelta(days=1)
        self.lojista.save()
        self._roda_comando()
        self.assertIn('amanhã', mail.outbox[0].subject)

    def test_email_depois_d3(self):
        self.lojista.trial_fim = date.today() - timedelta(days=3)
        self.lojista.save()
        self._roda_comando()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('pausada', mail.outbox[0].subject)

    def test_nao_reenvia_o_mesmo_aviso(self):
        self.lojista.trial_fim = date.today() - timedelta(days=3)
        self.lojista.save()
        self._roda_comando()
        self._limpa_caixa()
        self._roda_comando()
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(TrialAviso.objects.filter(lojista=self.lojista).count(), 1)

    def test_nao_avisa_quem_pagou(self):
        self.lojista.status_assinatura = 'ativa'
        self.lojista.trial_fim = date.today() - timedelta(days=5)
        self.lojista.save()
        self._roda_comando()
        self.assertEqual(len(mail.outbox), 0)

    def test_nao_manda_email_no_d2_ou_d4(self):
        for dias in (2, 4, 6, 8, 9):
            self.lojista.trial_fim = date.today() - timedelta(days=dias)
            self.lojista.save()
            self._roda_comando()
        self.assertEqual(len(mail.outbox), 0)
