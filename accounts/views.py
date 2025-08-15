# accounts/views.py
import logging
import random
import string

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash

from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    FirstPasswordChangeForm
)
from .utils import send_welcome_email
from .models import CustomUser

# Configura o logger para este módulo
logger = logging.getLogger(__name__)


def generate_random_password(length=12):
    """Gera uma senha aleatória segura"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(chars) for _ in range(length))


def register_view(request):
    """
    View para registro de novos usuários com envio de senha por e-mail
    """
    if request.user.is_authenticated:
        logger.info('Usuário autenticado tentou acessar a página de registro. Redirecionando para a home.')
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            logger.info('Tentativa de cadastro com dados válidos.')
            
            # Gera senha aleatória
            password = generate_random_password()
            
            # Cria usuário sem salvar ainda
            user = form.save(commit=False)
            user.set_password(password)
            user.must_change_password = True
            user.save()
            
            # Envia e-mail com a senha
            try:
                send_welcome_email(user, password)
                messages.success(
                    request,
                    'Cadastro realizado com sucesso! Verifique seu e-mail para a senha de acesso.'
                )
                logger.info(f'Novo usuário cadastrado com sucesso: {user.email}. E-mail de boas-vindas enviado.')
            except Exception as e:
                # Loga o erro detalhado do envio de e-mail
                logger.error(f'Cadastro realizado para {user.email}, mas falha ao enviar o e-mail de boas-vindas: {e}', exc_info=True)
                messages.warning(
                    request,
                    f'Cadastro realizado, mas ocorreu um erro ao enviar o e-mail.'
                )
            
            return redirect('accounts:login')
        else:
            # Loga os erros de validação do formulário
            logger.warning(f'Tentativa de cadastro com dados inválidos. Erros: {form.errors.as_json()}')
            # O template HTML já mostra a mensagem genérica de erro
            # messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = CustomUserCreationForm()
        logger.info('Página de registro acessada via GET.')

    return render(request, 'accounts/register.html', {
        'form': form,
        'title': 'Cadastro de Novo Usuário'
    })


def login_view(request):
    """
    View personalizada para login com redirecionamento para alteração de senha
    quando necessário
    """
    if request.user.is_authenticated:
        logger.info('Usuário autenticado tentou acessar a página de login. Redirecionando para a home.')
        return redirect('home')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                if user.must_change_password:
                    messages.info(request, 'Você deve alterar sua senha antes de continuar.')
                    logger.info(f'Usuário {user.email} logado pela primeira vez. Redirecionando para alteração de senha.')
                    return redirect('accounts:change_password')
                
                messages.success(request, f'Bem-vindo(a), {user.first_name}!')
                next_url = request.GET.get('next', 'home')
                logger.info(f'Usuário {user.email} logado com sucesso. Redirecionando para {next_url}.')
                return redirect(next_url)
            else:
                # Falha na autenticação
                messages.error(request, 'E-mail ou senha incorretos.')
                logger.warning('Falha na autenticação. E-mail ou senha incorretos.')
        else:
            # Falha de validação do formulário (ex: campos vazios)
            logger.warning(f'Tentativa de login com formulário inválido. Erros: {form.errors.as_json()}')
            messages.error(request, 'E-mail ou senha incorretos.')
    else:
        form = CustomAuthenticationForm()
        logger.info('Página de login acessada via GET.')

    return render(request, 'accounts/login.html', {
        'form': form,
        'title': 'Login'
    })


@login_required
def change_password_view(request):
    """
    View para alteração de senha obrigatória no primeiro acesso
    """
    if not request.user.must_change_password:
        logger.info(f'Usuário {request.user.email} tentou acessar a alteração de senha, mas não é obrigatória. Redirecionando para a home.')
        return redirect('home')

    if request.method == 'POST':
        form = FirstPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.must_change_password = False
            user.save()
            
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Senha alterada com sucesso!')
            logger.info(f'Senha do usuário {user.email} alterada com sucesso.')
            return redirect('home')
        else:
            logger.warning(f'Tentativa de alteração de senha inválida para o usuário {request.user.email}. Erros: {form.errors.as_json()}')
    else:
        form = FirstPasswordChangeForm(request.user)
        logger.info(f'Página de alteração de senha obrigatória acessada por {request.user.email}.')

    return render(request, 'accounts/change_password.html', {
        'form': form,
        'title': 'Alteração de Senha Obrigatória'
    })


@login_required
def logout_view(request):
    """
    View para logout seguro
    """
    logger.info(f'Usuário {request.user.email} realizando logout.')
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('accounts:login')


# Em Finanças_Pessoais/accounts/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def home_view(request):
    return render(request, 'home.html')