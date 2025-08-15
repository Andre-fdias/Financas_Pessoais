from django import forms
from django.contrib.auth.models import User
from .models import BankAccount, CreditCard, Transaction, Budget
from .models import BANK_CHOICES, ACCOUNT_TYPE_CHOICES, CARD_FLAG_CHOICES
from .models import TRANSACTION_TYPE_CHOICES, EXPENSE_CATEGORY_CHOICES
from .models import PAYMENT_METHOD_CHOICES, RECURRENCE_CHOICES
from django.core.validators import MinValueValidator
from django.utils import timezone


class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['bank', 'account_type', 'agency', 'account_number', 'owner', 'opening_balance', 'opening_date', 'is_active', 'notes']
        widgets = {
            'opening_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'is_active': 'Conta ativa?',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['bank'].widget.attrs.update({'class': 'form-select'})
        self.fields['account_type'].widget.attrs.update({'class': 'form-select'})
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class CreditCardForm(forms.ModelForm):
    class Meta:
        model = CreditCard
        fields = ['card_name', 'card_flag', 'card_number', 'owner', 'limit', 'due_day', 'closing_day', 'is_active', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'is_active': 'Cartão ativo?',
            'card_number': 'Últimos 4 dígitos',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['card_flag'].widget.attrs.update({'class': 'form-select'})
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount', 'date', 'description', 'category', 
                 'subcategory', 'payment_method', 'is_recurrent', 'recurrence',
                 'installments', 'account', 'credit_card', 'location', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.TextInput(attrs={'placeholder': 'Descrição da transação'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observações adicionais'}),
            'is_recurrent': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar contas e cartões apenas do usuário atual
        if self.user:
            self.fields['account'].queryset = BankAccount.objects.filter(user=self.user, is_active=True)
            self.fields['credit_card'].queryset = CreditCard.objects.filter(user=self.user, is_active=True)
        
        # Adicionar classes CSS aos campos
        for field in self.fields:
            if field in ['transaction_type', 'category', 'payment_method', 'recurrence', 'account', 'credit_card']:
                self.fields[field].widget.attrs.update({'class': 'form-select'})
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Definir valores iniciais
        self.fields['date'].initial = timezone.now().date()
        self.fields['transaction_type'].initial = 'OUT'
        
    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get('transaction_type')
        account = cleaned_data.get('account')
        credit_card = cleaned_data.get('credit_card')
        
        # Validar que transações de saída têm conta ou cartão associado
        if transaction_type == 'OUT' and not account and not credit_card:
            raise forms.ValidationError("Para transações de saída, é necessário informar uma conta ou cartão de crédito.")
        
        return cleaned_data
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'amount', 'period', 'start_date', 'end_date', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['category'].widget.attrs.update({'class': 'form-select'})
        self.fields['period'].widget.attrs.update({'class': 'form-select'})
        
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if end_date and end_date < start_date:
            raise forms.ValidationError("A data final não pode ser anterior à data inicial.")
        
        return cleaned_data
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class TransactionFilterForm(forms.Form):
    start_date = forms.DateField(
        label='Data inicial',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    end_date = forms.DateField(
        label='Data final',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    transaction_type = forms.ChoiceField(
        label='Tipo',
        choices=[('', 'Todos')] + TRANSACTION_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ChoiceField(
        label='Categoria',
        choices=[('', 'Todas')] + EXPENSE_CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    account = forms.ModelChoiceField(
        label='Conta',
        queryset=BankAccount.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    credit_card = forms.ModelChoiceField(
        label='Cartão',
        queryset=CreditCard.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    payment_method = forms.ChoiceField(
        label='Forma de pagamento',
        choices=[('', 'Todas')] + PAYMENT_METHOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_recurrent = forms.BooleanField(
        label='Apenas recorrentes',
        required=False,
        widget=forms.CheckboxInput()
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['account'].queryset = BankAccount.objects.filter(user=user)
            self.fields['credit_card'].queryset = CreditCard.objects.filter(user=user)