from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogo', '0004_lojista_link_app_habilitado_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lojista',
            name='logo',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='logos_loja/',
                verbose_name='Logo da loja',
                help_text='Usada no ícone do app instalável (PWA). Se vazia, uma inicial colorida é gerada automaticamente.',
            ),
        ),
    ]
