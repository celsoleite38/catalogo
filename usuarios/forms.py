from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


def limpar_cnpj(valor):
    if not valor:
        return ''
    return ''.join(c for c in valor if c.isdigit())


def formatar_cnpj(digitos):
    digitos = limpar_cnpj(digitos)
    if len(digitos) != 14:
        return digitos
    return f"{digitos[0:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:14]}"


class CadastroForm(forms.Form):
    email = forms.EmailField(
        label='Email (seu usuário)',
        widget=forms.EmailInput(attrs={
            'class': 'w-full p-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'voce@exemplo.com.br',
        }),
    )
    senha = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Crie uma senha',
        }),
    )
    confirmar_senha = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Repita a senha',
        }),
    )

    def clean(self):
        cleaned = super().clean()
        senha = cleaned.get('senha')
        confirmar = cleaned.get('confirmar_senha')

        if senha and confirmar and senha != confirmar:
            raise forms.ValidationError('As senhas informadas não conferem.')

        if senha:
            try:
                validate_password(senha)
            except ValidationError as e:
                raise forms.ValidationError(list(e.messages))

        return cleaned

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError(
                'Já existe um cadastro com este email. Faça login ou verifique sua caixa de entrada (confirmação).'
            )
        return email


class PerfilForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.logo_obrigatoria = kwargs.pop('logo_obrigatoria', True)
        super().__init__(*args, **kwargs)

    nome_loja = forms.CharField(
        label='Nome da loja',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none',
            'placeholder': 'Ex: Pizzaria Bella Napoli',
        }),
    )
    cnpj = forms.CharField(
        label='CNPJ',
        max_length=18,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none',
            'placeholder': '00.000.000/0000-00',
            'inputmode': 'numeric',
        }),
    )
    logo = forms.ImageField(
        label='Logo da loja',
        required=False,
        error_messages={'required': 'A logo da loja é obrigatória.'},
        widget=forms.FileInput(attrs={
            'class': 'w-full p-2.5 border border-gray-300 rounded-lg bg-gray-50',
            'accept': 'image/png,image/jpeg,image/webp',
        }),
    )
    whatsapp = forms.CharField(
        label='WhatsApp (com DDD)',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none',
            'placeholder': 'Ex: 5535999998888',
        }),
    )

    MAX_LOGO_SIZE = 2 * 1024 * 1024

    def clean_cnpj(self):
        valor = limpar_cnpj(self.cleaned_data.get('cnpj'))
        if len(valor) != 14:
            raise forms.ValidationError('CNPJ inválido. Informe os 14 dígitos.')
        return formatar_cnpj(valor)

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo and hasattr(logo, 'size') and logo.size > self.MAX_LOGO_SIZE:
            raise forms.ValidationError('A logo não pode exceder 2MB.')
        return logo

    def clean(self):
        cleaned = super().clean()
        if self.logo_obrigatoria and not cleaned.get('logo'):
            self.add_error('logo', 'A logo da loja é obrigatória.')
        return cleaned