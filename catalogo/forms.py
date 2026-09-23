from django import forms
from .models import Produto, Categoria, VariacaoProduto, Lojista, TipoVariacao


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'ordem']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none',
                'placeholder': 'Ex: Calçados, Camisetas, Acessórios'
            }),
            'ordem': forms.NumberInput(attrs={
                'class': 'w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none',
                'placeholder': '0'
            }),
        }

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['categoria', 'nome', 'descricao', 'preco_base', 'foto', 'foto2', 'ativo']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-green-500 bg-white'}),
            'nome': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-green-500', 'placeholder': 'Ex: Camiseta Algodão Premium'}),
            'descricao': forms.Textarea(attrs={'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-green-500', 'rows': 3, 'placeholder': 'Descrição detalhada do produto...'}),
            'preco_base': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-green-500', 'step': '0.01'}),
            'foto': forms.FileInput(attrs={'class': 'w-full p-2 border rounded-lg bg-gray-50', 'onchange': 'validarTamanhoFoto(this)'}),
            'foto2': forms.FileInput(attrs={'class': 'w-full p-2 border rounded-lg bg-gray-50', 'onchange': 'validarTamanhoFoto(this)'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-green-600 rounded border-gray-300 focus:ring-green-500'}),
        }

    MAX_SIZE = 2 * 1024 * 1024

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')
        if foto and foto.size > self.MAX_SIZE:
            raise forms.ValidationError('A foto principal não pode exceder 2MB.')
        return foto

    def clean_foto2(self):
        foto2 = self.cleaned_data.get('foto2')
        if foto2 and foto2.size > self.MAX_SIZE:
            raise forms.ValidationError('A foto secundária não pode exceder 2MB.')
        return foto2

    def __init__(self, *args, **kwargs):
        lojista = kwargs.pop('lojista', None)
        super().__init__(*args, **kwargs)
        # Exibe no dropdown apenas as categorias criadas por este lojista
        if lojista:
            self.fields['categoria'].queryset = Categoria.objects.filter(lojista=lojista)


class ConfiguracaoLojistaForm(forms.ModelForm):
    class Meta:
        model = Lojista
        fields = ['tema']
        widgets = {
            'tema': forms.Select(attrs={
                'class': 'w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-black focus:outline-none bg-white'
            }),
        }

class TipoVariacaoForm(forms.ModelForm):
    class Meta:
        model = TipoVariacao
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none',
                'placeholder': 'Ex: Tamanho, Cor, Sabor, Cobertura'
            }),
        }