from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import ContaBancaria, Entrada, Saida


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class ContaBancariaForm(forms.ModelForm):
    class Meta:
        model = ContaBancaria
        fields = ['nome_banco', 'tipo', 'agencia', 'numero_conta', 'saldo_atual',
                  'numero_cartao', 'limite_cartao', 'dia_fechamento_fatura',
                  'dia_vencimento_fatura', 'ativa']
        widgets = {
            'nome_banco': forms.Select(attrs={'class': 'form-input'}),
            'tipo': forms.Select(attrs={'class': 'form-input'}),
            'agencia': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '0000'}),
            'numero_conta': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '00000-0'}),
            'saldo_atual': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0,00'}),
            'numero_cartao': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '**** **** **** ****'}),
            'limite_cartao': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0,00'}),
            'dia_fechamento_fatura': forms.NumberInput(attrs={'class': 'form-input', 'min': '1', 'max': '31', 'placeholder': '1-31'}),
            'dia_vencimento_fatura': forms.NumberInput(attrs={'class': 'form-input', 'min': '1', 'max': '31', 'placeholder': '1-31'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')

        # Validações específicas para contas bancárias
        if tipo in ['corrente', 'poupanca']:
            if not cleaned_data.get('agencia'):
                self.add_error('agencia', 'Agência é obrigatória para este tipo de conta')
            if not cleaned_data.get('numero_conta'):
                self.add_error('numero_conta', 'Número da conta é obrigatório para este tipo de conta')

        # Validações específicas para cartão de crédito
        if tipo == 'cartao_credito':
            if not cleaned_data.get('limite_cartao'):
                self.add_error('limite_cartao', 'Limite do cartão é obrigatório para cartões de crédito')

        return cleaned_data


class EntradaForm(forms.ModelForm):
    class Meta:
        model = Entrada
        fields = ['nome', 'valor', 'data', 'local', 'forma_recebimento', 'conta_bancaria', 'observacao']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Descrição da entrada'
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0.01'
            }),
            'data': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'local': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Origem do recebimento'
            }),
            'forma_recebimento': forms.Select(attrs={
                'class': 'form-input'
            }),
            'conta_bancaria': forms.Select(attrs={
                'class': 'form-input'
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'Observações adicionais'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # Filtra apenas contas bancárias ativas do usuário
            self.fields['conta_bancaria'].queryset = ContaBancaria.objects.filter(
                proprietario=user,
                ativa=True
            )

    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if isinstance(valor, str):
            # Converte de formato brasileiro para decimal
            valor = valor.replace('.', '').replace(',', '.')
            try:
                return Decimal(valor)
            except (InvalidOperation, ValueError):
                raise forms.ValidationError("Valor inválido")
        return valor


class SaidaForm(forms.ModelForm):
    class Meta:
        model = Saida
        fields = [
            'nome', 'valor', 'valor_parcela', 'data_lancamento', 'data_vencimento', 'local',
            'categoria', 'subcategoria', 'forma_pagamento', 'tipo_pagamento_detalhe',
            'situacao', 'quantidade_parcelas', 'recorrente', 'observacao', 'conta_bancaria'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nome da transação'}),
            'valor': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0.01'}),
            'valor_parcela': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'readonly': 'readonly'}),
            'data_lancamento': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'max': timezone.now().date().isoformat()}),
            'data_vencimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'min': timezone.now().date().isoformat()}),
            'local': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Local'}),
            'categoria': forms.Select(attrs={'class': 'form-input'}),
            'subcategoria': forms.Select(attrs={'class': 'form-input'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-input'}),
            'tipo_pagamento_detalhe': forms.Select(attrs={'class': 'form-input'}),
            'situacao': forms.Select(attrs={'class': 'form-input'}),
            'quantidade_parcelas': forms.NumberInput(attrs={'class': 'form-input', 'min': '1'}),
            'recorrente': forms.Select(attrs={'class': 'form-input'}),
            'observacao': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Observações adicionais'}),
            'conta_bancaria': forms.Select(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['conta_bancaria'].queryset = ContaBancaria.objects.filter(proprietario=user, ativa=True)
        # Opcional: se usar categorias/subcategorias do usuário, pode filtrar assim:
        # self.fields['categoria'].queryset = Categoria.objects.filter(usuario=user)
        # self.fields['subcategoria'].queryset = Subcategoria.objects.filter(usuario=user)

    def clean(self):
        cleaned_data = super().clean()
        data_lancamento = cleaned_data.get('data_lancamento')
        situacao = cleaned_data.get('situacao')
        tipo_pagamento = cleaned_data.get('tipo_pagamento_detalhe')

        # Segurança: converte datetime para date
        if data_lancamento and hasattr(data_lancamento, 'date'):
            data_lancamento = data_lancamento.date()

        # Validação de data de lançamento
        if data_lancamento and data_lancamento > timezone.now().date():
            raise ValidationError({'data_lancamento': 'Data de lançamento não pode ser futura.'})

        # Se for à vista e pago, data de vencimento deve ser igual a data de lançamento
        if tipo_pagamento == 'avista' and situacao == 'pago':
            cleaned_data['data_vencimento'] = data_lancamento

        return cleaned_data
