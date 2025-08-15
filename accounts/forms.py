from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm, 
    PasswordChangeForm
)
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re

User = get_user_model()

class CustomUserCreationForm(forms.ModelForm):
    # Validador de CPF
    cpf_validator = RegexValidator(
        regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
        message='CPF deve estar no formato: 000.000.000-00'
    )
    
    # Campos do formulário
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Nome'
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Sobrenome'
    )
    
    cpf = forms.CharField(
        max_length=14,
        required=True,
        validators=[cpf_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00'
        }),
        label='CPF'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label='E-mail'
    )
    
    data_nascimento = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Data de Nascimento'
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'cpf', 'email', 'data_nascimento')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este e-mail já está cadastrado.")
        return email
    
    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        # Remove caracteres não numéricos
        cpf_numeros = re.sub(r'[^0-9]', '', cpf)
        
        # Verifica se tem 11 dígitos
        if len(cpf_numeros) != 11:
            raise ValidationError("CPF deve conter 11 dígitos.")
        
        # Verifica dígitos repetidos (000.000.000-00)
        if len(set(cpf_numeros)) == 1:
            raise ValidationError("CPF inválido.")
            
        return cpf

    def save(self, commit=True):
        """
        Sobrescreve o método save para não lidar com senhas.
        """
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="E-mail",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    
    error_messages = {
        'invalid_login': "E-mail ou senha inválidos.",
        'inactive': "Esta conta está inativa.",
    }

class FirstPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget = forms.HiddenInput()
        self.fields['old_password'].required = False
        
        # Personaliza os campos
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'new-password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'new-password'
        })
    
    def clean_old_password(self):
        # Ignora a validação da senha antiga
        return ""