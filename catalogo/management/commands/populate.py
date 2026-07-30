import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.conf import settings
from catalogo.models import Lojista, Categoria, Produto, TipoVariacao, ValorVariacao, VariacaoProduto

BASE_DIR = settings.BASE_DIR
MEDIA_PRODUTOS = os.path.join(settings.MEDIA_ROOT, 'produtos')


def criar_foto_copia(loja_slug, filename):
    origem = os.path.join(MEDIA_PRODUTOS, loja_slug, filename)
    if os.path.exists(origem):
        rel_path = os.path.join('produtos', loja_slug, filename)
        return rel_path
    return None


class Command(BaseCommand):
    help = 'Popula o banco com dados de demonstração'

    def handle(self, *args, **options):
        self.stdout.write('Populando banco de dados...\n')

        # ─── SUPERUSER ───────────────────────────────────────────────
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@innosoft.com.br', 'admin')
            self.stdout.write('  ✓ Superuser "admin" (senha: admin)')

        # ─── LOJISTAS ────────────────────────────────────────────────
        lojas_data = [
            {
                'username': 'acai',
                'user_pass': 'acai123',
                'nome_loja': 'Açai Saúde',
                'slug': 'acai-saude',
                'whatsapp': '5535999998888',
                'tema': 'mint_fresh',
                'media_slug': 'acai-saude',
                'categorias': ['Açaís Tradicionais', 'Açaís Especiais', 'Sorvetes'],
                'produtos': [
                    {'nome': 'Açai Tradicional 500ml', 'preco': 18.90, 'cat': 0, 'foto': 'açaí_tradicional.jpg', 'desc': 'Açai puro com granola, banana e mel'},
                    {'nome': 'Açai com Cupuaçu 500ml', 'preco': 22.90, 'cat': 1, 'foto': 'açaí_com_cupuaçu.jpg', 'desc': 'Açai batido com cupuaçu e coberturas'},
                    {'nome': 'Sorvete de Creme com Calda', 'preco': 14.90, 'cat': 2, 'foto': 'sorvete_de_creme_com_calda.jpg', 'desc': 'Sorvete artesanal de creme com calda quente'},
                ],
            },
            {
                'username': 'pizzaria',
                'user_pass': 'pizza123',
                'nome_loja': 'Pizzaria Bella Napoli',
                'slug': 'pizzaria-bella-napoli',
                'whatsapp': '5535988887777',
                'tema': 'warm_sunset',
                'media_slug': 'pizzaria-bella-napoli',
                'categorias': ['Pizzas Salgadas', 'Pizzas Doces'],
                'produtos': [
                    {'nome': 'Pizza Margherita', 'preco': 42.90, 'cat': 0, 'foto': 'pizza_margherita.jpg', 'desc': 'Molho, mussarela, manjericão e parmesão'},
                    {'nome': 'Pizza Calabresa', 'preco': 45.90, 'cat': 0, 'foto': 'pizza_calabresa.jpg', 'desc': 'Calabresa fatiada, cebola e azeitona'},
                    {'nome': 'Pizza Frango com Catupiry', 'preco': 49.90, 'cat': 0, 'foto': 'pizza_frango_com_catupiry.jpg', 'desc': 'Frango desfiado com catupiry cremoso'},
                    {'nome': 'Pizza Portuguesa', 'preco': 47.90, 'cat': 0, 'foto': 'pizza_portuguesa.jpg', 'desc': 'Presunto, ovos, cebola, pimentão e mussarela'},
                    {'nome': 'Pizza Chocolate com Morango', 'preco': 52.90, 'cat': 1, 'foto': 'pizza_chocolate_com_morango.jpg', 'desc': 'Chocolate ao leite com morangos frescos'},
                ],
            },
            {
                'username': 'tecnofit',
                'user_pass': 'techo123',
                'nome_loja': 'TecnoFit Gear',
                'slug': 'tecnofit-gear',
                'whatsapp': '5535977776666',
                'tema': 'sport_fire',
                'media_slug': 'tecnofit-gear',
                'categorias': ['Equipamentos', 'Vestuário', 'Acessórios'],
                'produtos': [
                    {'nome': 'Smartband Sport Pro V2', 'preco': 199.90, 'cat': 0, 'foto': 'smartband_sport_pro_v2.jpg', 'desc': 'Monitor cardíaco, GPS e resistente à água'},
                    {'nome': 'Legging Fitness Pro', 'preco': 129.90, 'cat': 1, 'foto': 'legging_fitness_pro.jpg', 'desc': 'Tecido dry-fit com compressão graduada'},
                    {'nome': 'Garrafa Térmica Inox 1L', 'preco': 79.90, 'cat': 2, 'foto': 'garrafa_térmica_inox_1l.jpg', 'desc': 'Aço inox dupla parede, mantém 12h gelado'},
                ],
            },
            {
                'username': 'urbanstyle',
                'user_pass': 'urban123',
                'nome_loja': 'Urban Style Co.',
                'slug': 'urban-style-co',
                'whatsapp': '5534966665555',
                'tema': 'dark_neon',
                'media_slug': 'urban-style-co',
                'categorias': ['Camisetas', 'Calçados', 'Acessórios', 'Mochilas'],
                'produtos': [
                    {'nome': 'Camiseta Oversized Minimalist', 'preco': 89.90, 'cat': 0, 'foto': 'camiseta_oversized_minimalist.jpg', 'desc': 'Algodão premium, corte oversized, neutro'},
                    {'nome': 'Tênis Streetwear White Minimal', 'preco': 249.90, 'cat': 1, 'foto': 'tênis_streetwear_white_minimal.jpg', 'desc': 'Design minimalista, solado tratorado'},
                    {'nome': 'Boné Aba Curva Premium', 'preco': 69.90, 'cat': 2, 'foto': 'boné_aba_curva_premium.jpg', 'desc': 'Algodão estruturado, aba curva ajustável'},
                    {'nome': 'Óculos de Sol Retro Oval', 'preco': 149.90, 'cat': 2, 'foto': 'óculos_de_sol_retro_oval.jpg', 'desc': 'Estilo retrô com lentes UV400 polarizadas'},
                    {'nome': 'Mochila Urbana Roll-Top', 'preco': 189.90, 'cat': 3, 'foto': 'mochila_urbana_roll-top.jpg', 'desc': 'Impermeável, 25L, notebook até 15.6"'},
                ],
            },
            {
                'username': 'econature',
                'user_pass': 'eco123',
                'nome_loja': 'EcoNature Organics',
                'slug': 'econature-organics',
                'whatsapp': '5534955554444',
                'tema': 'modern_emerald',
                'media_slug': 'econature-organics',
                'categorias': ['Difusores', 'Sabonetes', 'Velas'],
                'produtos': [
                    {'nome': 'Difusor de Aromas Capim-Limão', 'preco': 59.90, 'cat': 0, 'foto': 'difusor_de_aromas_capim-limão.jpg', 'desc': 'Essência natural de capim-limão com varetas de bambu'},
                ],
            },
        ]

        for ld in lojas_data:
            user, created = User.objects.get_or_create(
                username=ld['username'],
                defaults={'email': f'{ld["username"]}@email.com'},
            )
            if created:
                user.set_password(ld['user_pass'])
                user.save()
                self.stdout.write(f'  ✓ Usuário "{ld["username"]}" (senha: {ld["user_pass"]})')

            lojista, created = Lojista.objects.get_or_create(
                slug=ld['slug'],
                defaults={
                    'user': user,
                    'nome_loja': ld['nome_loja'],
                    'whatsapp': ld['whatsapp'],
                    'tema': ld['tema'],
                },
            )
            if created:
                self.stdout.write(f'  ✓ Loja "{ld["nome_loja"]}"')

            # Categorias
            cat_map = {}
            for i, nome_cat in enumerate(ld['categorias']):
                cat, _ = Categoria.objects.get_or_create(
                    lojista=lojista, nome=nome_cat,
                    defaults={'ordem': i},
                )
                cat_map[i] = cat

            # Produtos
            for pd in ld['produtos']:
                foto = criar_foto_copia(ld['media_slug'], pd['foto'])
                produto, created = Produto.objects.get_or_create(
                    lojista=lojista, nome=pd['nome'],
                    defaults={
                        'categoria': cat_map[pd['cat']],
                        'preco_base': pd['preco'],
                        'descricao': pd.get('desc', ''),
                        'ativo': True,
                    },
                )
                if created and foto:
                    produto.foto.name = foto
                    produto.save(update_fields=['foto'])
                    self.stdout.write(f'    ✓ {pd["nome"]} (R$ {pd["preco"]})')

            # Valores de variação padrão por loja
            tipo_tamanho = TipoVariacao.objects.filter(lojista=lojista, nome='Tamanho').first()
            tipo_cor = TipoVariacao.objects.filter(lojista=lojista, nome='Cor').first()

            if tipo_tamanho:
                for tam in ['P', 'M', 'G', 'GG']:
                    ValorVariacao.objects.get_or_create(tipo=tipo_tamanho, nome=tam)

            if tipo_cor:
                for cor in ['Preto', 'Branco', 'Azul']:
                    ValorVariacao.objects.get_or_create(tipo=tipo_cor, nome=cor)

            # Variações específicas por loja
            loja_slug = ld['slug']
            if loja_slug == 'acai-saude' and tipo_tamanho:
                for p in Produto.objects.filter(lojista=lojista):
                    for tam in ['300ml', '500ml', '700ml']:
                        vv, _ = ValorVariacao.objects.get_or_create(tipo=tipo_tamanho, nome=tam)
                        adicional = 0 if tam == '300ml' else 4 if tam == '500ml' else 8
                        VariacaoProduto.objects.get_or_create(
                            produto=p, tipo=tipo_tamanho, valor=tam,
                            defaults={'preco_adicional': adicional},
                        )

            if loja_slug == 'pizzaria-bella-napoli':
                tipo_borda = TipoVariacao.objects.filter(lojista=lojista, nome__icontains='borda').first()
                if not tipo_borda:
                    tipo_borda, _ = TipoVariacao.objects.get_or_create(lojista=lojista, nome='Borda')
                for borda in ['Tradicional', 'Catupiry', 'Cheddar']:
                    ValorVariacao.objects.get_or_create(tipo=tipo_borda, nome=borda)
                for p in Produto.objects.filter(lojista=lojista):
                    for borda in ['Tradicional', 'Catupiry', 'Cheddar']:
                        adicional = 0 if borda == 'Tradicional' else 6
                        VariacaoProduto.objects.get_or_create(
                            produto=p, tipo=tipo_borda, valor=borda,
                            defaults={'preco_adicional': adicional},
                        )

            if loja_slug == 'tecnofit-gear':
                for p in Produto.objects.filter(lojista=lojista):
                    if tipo_cor:
                        for cor in ['Preto', 'Azul', 'Vermelho']:
                            vv, _ = ValorVariacao.objects.get_or_create(tipo=tipo_cor, nome=cor)
                            VariacaoProduto.objects.get_or_create(
                                produto=p, tipo=tipo_cor, valor=cor,
                                defaults={'preco_adicional': 0},
                            )
                    if tipo_tamanho:
                        for tam in ['P', 'M', 'G']:
                            vv, _ = ValorVariacao.objects.get_or_create(tipo=tipo_tamanho, nome=tam)
                            VariacaoProduto.objects.get_or_create(
                                produto=p, tipo=tipo_tamanho, valor=tam,
                                defaults={'preco_adicional': 0 if tam == 'M' else -5 if tam == 'P' else 10},
                            )

        # ─── RESUMO ──────────────────────────────────────────────────
        self.stdout.write('\n═══ RESUMO ═══')
        self.stdout.write(f'  Usuários:  {User.objects.count()}')
        self.stdout.write(f'  Lojas:     {Lojista.objects.count()}')
        self.stdout.write(f'  Categorias:{Categoria.objects.count()}')
        self.stdout.write(f'  Produtos:  {Produto.objects.count()}')
        self.stdout.write(f'  Variações: {VariacaoProduto.objects.count()}')
        self.stdout.write(f'\n  Admin:     /admin/   (admin / admin)')
        for ld in lojas_data:
            lojista = Lojista.objects.filter(slug=ld['slug']).first()
            if lojista:
                self.stdout.write(f'  Catálogo:  /{lojista.slug}/')
        self.stdout.write('\nPopulado com sucesso!')
