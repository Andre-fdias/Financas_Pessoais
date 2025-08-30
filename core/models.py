from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from decimal import Decimal
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
import os
import re

from .choices import (
    PERIODICIDADE_CHOICES, FORMA_RECEBIMENTO_CHOICES, FORMA_PAGAMENTO_CHOICES,
    TIPO_PAGAMENTO_DETALHE_CHOICES, SITUACAO_CHOICES, TIPO_CONTA_CHOICES, 
    BANCO_CHOICES, CATEGORIA_CHOICES, SUBCATEGORIA_CHOICES, THEME_CHOICES
)


class BaseModel(models.Model):
    """Modelo base com campos comuns"""
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class ContaBancaria(BaseModel):
    """
    Representa uma conta bancária ou cartão associado a um usuário.
    Pode ser uma conta corrente, poupança, cartão de crédito, etc.
    """
    proprietario = models.ForeignKey(User, on_delete=models.CASCADE)
    nome_banco = models.CharField(max_length=20, choices=BANCO_CHOICES)
    nome_do_titular = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name="Nome do Titular da Conta",
        help_text="Nome do titular real da conta (ex: filho, cônjuge), se diferente do usuário gestor."
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CONTA_CHOICES, verbose_name="Tipo de Conta")
    agencia = models.CharField(max_length=10, blank=True, null=True)
    numero_conta = models.CharField(max_length=20, blank=True, null=True)
    saldo_atual = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    ativa = models.BooleanField(default=True)
    
    # Campos específicos para cartão de crédito
    numero_cartao = models.CharField(max_length=20, blank=True, null=True)
    limite_cartao = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    dia_fechamento_fatura = models.PositiveSmallIntegerField(blank=True, null=True)
    dia_vencimento_fatura = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = 'Conta Bancária'
        verbose_name_plural = 'Contas Bancárias'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['proprietario', 'ativa']),
            models.Index(fields=['tipo']),
        ]

    def __str__(self):
        display_name = self.get_nome_banco_display()
        if self.tipo in ['credito', 'debito', 'alimentacao']:
            return f"{display_name} - {self.numero_conta or self.numero_cartao}"
        return f"{display_name} - {self.agencia}/{self.numero_conta}"
    
    def saldo_formatado(self):
        return f"R$ {self.saldo_atual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    def is_cartao_credito(self):
        return self.tipo == 'credito'

    def clean(self):
        super().clean()
        if self.tipo in ['corrente', 'poupanca']:
            if not self.agencia:
                raise ValidationError({'agencia': 'Agência é obrigatória para contas correntes e poupança.'})
            if not self.numero_conta:
                raise ValidationError({'numero_conta': 'Número da conta é obrigatório para contas correntes e poupança.'})
        elif self.tipo in ['credito', 'debito', 'alimentacao'] and self.agencia:
            raise ValidationError({'agencia': 'Agência não é aplicável para este tipo de conta.'})


class Categoria(BaseModel):
    """
    Representa uma categoria de transação (Entrada ou Saída) criada pelo usuário.
    Ex: Moradia, Alimentação, Salário.
    """
    nome = models.CharField(max_length=100)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        unique_together = ('nome', 'usuario')
        indexes = [
            models.Index(fields=['usuario', 'nome']),
        ]

    def __str__(self):
        return self.nome


class Subcategoria(BaseModel):
    """
    Representa uma subcategoria dentro de uma Categoria, criada pelo usuário.
    Ex: Aluguel (dentro de Moradia), Supermercado (dentro de Alimentação).
    """
    nome = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='subcategorias')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Subcategoria"
        verbose_name_plural = "Subcategorias"
        unique_together = ('nome', 'categoria', 'usuario')
        indexes = [
            models.Index(fields=['usuario', 'categoria']),
        ]

    def __str__(self):
        return f"{self.nome} ({self.categoria.nome})"


class Entrada(BaseModel):
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='entradas',
        verbose_name="Usuário"
    )
    conta_bancaria = models.ForeignKey(
        ContaBancaria, 
        on_delete=models.CASCADE,
        verbose_name="Conta Bancária"
    )
    nome = models.CharField(
        max_length=255,
        verbose_name="Descrição da Entrada"
    )
    valor = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Valor"
    )
    data = models.DateField(
        default=timezone.now,
        verbose_name="Data de Recebimento"
    )
    
    # Campos de detalhamento
    local = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Local/Origem"
    )
    
    # Campo de forma de recebimento
    forma_recebimento = models.CharField(
        max_length=20,
        choices=FORMA_RECEBIMENTO_CHOICES,
        default='dinheiro',
        verbose_name="Forma de Recebimento"
    )
    
    # Campo de observações
    observacao = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )

    class Meta:
        verbose_name = "Entrada"
        verbose_name_plural = "Entradas"
        ordering = ['-data', '-data_criacao']
        indexes = [
            models.Index(fields=['usuario', 'data']),
            models.Index(fields=['conta_bancaria', 'data']),
        ]

    def __str__(self):
        return f"{self.nome} - R$ {self.valor} ({self.data.strftime('%d/%m/%Y')})"

    def clean(self):
        super().clean()
        # Validação de data futura
        if self.data > timezone.now().date():
            raise ValidationError({
                'data': 'Não é possível registrar uma entrada com data futura.'
            })

    @property
    def valor_formatado(self):
        return f"R$ {self.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    @property
    def banco_origem(self):
        return self.conta_bancaria.get_nome_banco_display()


class Saida(BaseModel):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    conta_bancaria = models.ForeignKey(ContaBancaria, on_delete=models.CASCADE)
    nome = models.CharField(max_length=255, verbose_name="Nome da Transação")
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    data_lancamento = models.DateField(default=timezone.now, verbose_name="Data de Lançamento")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    local = models.CharField(max_length=100, blank=True, null=True, verbose_name="Local")
    
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Categoria"
    )
    
    subcategoria = models.ForeignKey(
        Subcategoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Subcategoria"
    )
    
    forma_pagamento = models.CharField(
        max_length=20,
        choices=FORMA_PAGAMENTO_CHOICES,
        default='dinheiro'
    )
    
    tipo_pagamento_detalhe = models.CharField(
        max_length=10,
        choices=TIPO_PAGAMENTO_DETALHE_CHOICES,
        default='avista'
    )
    
    situacao = models.CharField(
        max_length=10,
        choices=SITUACAO_CHOICES,
        default='pendente'
    )
    
    quantidade_parcelas = models.IntegerField(default=1)
    recorrente = models.CharField(
        max_length=10,
        choices=PERIODICIDADE_CHOICES,
        default='unica'
    )
    
    valor_parcela = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Valor da Parcela"
    )
    
    observacao = models.TextField(blank=True, null=True)

    class Meta: 
        ordering = ['-data_lancamento']
        verbose_name = "Saída"
        verbose_name_plural = "Saídas"
        indexes = [
            models.Index(fields=['usuario', 'data_lancamento']),
            models.Index(fields=['data_vencimento']),
            models.Index(fields=['situacao']),
        ]

    def __str__(self):
        return f"{self.nome} - R$ {self.valor}"

    def clean(self):
        super().clean()
        
        # Aceita tanto datetime quanto date
        data_lancamento = self.data_lancamento
        if isinstance(data_lancamento, datetime):
            data_lancamento = data_lancamento.date()

        # Validação para data de lançamento não pode ser futura
        if data_lancamento and data_lancamento > timezone.now().date():
            raise ValidationError({
                'data_lancamento': 'Data de lançamento não pode ser futura.'
            })
            
        # Se for à vista e pago, data de vencimento deve ser igual a data de lançamento
        if self.tipo_pagamento_detalhe == 'avista' and self.situacao == 'pago':
            if self.data_vencimento != data_lancamento:
                self.data_vencimento = data_lancamento
                
        # Validações de parcelamento
        if self.tipo_pagamento_detalhe == 'parcelado':
            if self.quantidade_parcelas <= 1:
                raise ValidationError({
                    'quantidade_parcelas': 'Para pagamento parcelado, o número de parcelas deve ser maior que 1.'
                })
            if not self.valor_parcela or self.valor_parcela == 0:
                self.valor_parcela = Decimal(self.valor) / Decimal(self.quantidade_parcelas)
                
            # Aceita diferença de até 1 centavo para questões de arredondamento
            soma_parcelas = self.valor_parcela * Decimal(self.quantidade_parcelas)
            if abs(soma_parcelas - Decimal(self.valor)) > Decimal('0.01'):
                raise ValidationError({
                    'valor_parcela': 'A soma das parcelas difere do valor total em mais de R$0,01.'
                })
                
        # Validação para recorrência
        if self.recorrente != 'unica' and self.tipo_pagamento_detalhe == 'parcelado':
            raise ValidationError({
                'recorrente': 'Não é possível ter recorrência em pagamentos parcelados.'
            })

    def save(self, *args, **kwargs):
        # Garante que o valor da parcela está correto antes de salvar
        if self.tipo_pagamento_detalhe == 'parcelado' and self.quantidade_parcelas > 1:
            self.valor_parcela = Decimal(self.valor) / Decimal(self.quantidade_parcelas)
        else:
            self.quantidade_parcelas = 1
            self.valor_parcela = self.valor
        
        # Se for à vista e pago, data de vencimento = data de lançamento
        if self.tipo_pagamento_detalhe == 'avista' and self.situacao == 'pago':
            self.data_vencimento = self.data_lancamento
        
        super().save(*args, **kwargs)
    
    @property
    def valor_mensal(self):
        """Retorna o valor que deve ser considerado no mês atual"""
        today = timezone.now().date()
        if self.situacao == 'pago' and self.data_lancamento.month == today.month:
            if self.tipo_pagamento_detalhe == 'avista':
                return self.valor
            else:
                return self.valor_parcela
        return Decimal('0.00')


class Profile(BaseModel):

    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    foto_perfil = models.ImageField(
        default='default.jpg',
        upload_to='profile_pics',
        verbose_name="Foto de Perfil"
    )
    theme = models.CharField(
        max_length=10, 
        choices=THEME_CHOICES, 
        default='light',
        verbose_name="Tema preferido"
    )
    password_updated_at = models.DateTimeField(null=True, blank=True)
    last_login_date = models.DateField(null=True, blank=True)
    login_streak = models.IntegerField(default=0)
    total_logins = models.IntegerField(default=0)

    def __str__(self):
        return f'Perfil de {self.user.username}'

    def save(self, *args, **kwargs):
        # Se está atualizando a foto e já existe uma foto anterior que não é a padrão
        if self.pk and self.foto_perfil and self.foto_perfil.name != 'default.jpg':
            try:
                old_profile = Profile.objects.get(pk=self.pk)
                if (old_profile.foto_perfil and 
                    old_profile.foto_perfil.name != 'default.jpg' and 
                    old_profile.foto_perfil.name != self.foto_perfil.name):
                    old_profile.foto_perfil.delete(save=False)
            except Profile.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Redimensionar imagem se existir e não for a padrão
        if self.foto_perfil and self.foto_perfil.name != 'default.jpg':
            try:
                img_path = self.foto_perfil.path
                if os.path.exists(img_path):
                    img = Image.open(img_path)
                    
                    # Redimensionar se for muito grande
                    if img.height > 300 or img.width > 300:
                        output_size = (300, 300)
                        img.thumbnail(output_size)
                        img.save(img_path)
            except Exception as e:
                print(f"Erro ao processar imagem: {e}")

    def update_login_streak(self):
        today = timezone.now().date()
        
        if self.last_login_date:
            days_since_last_login = (today - self.last_login_date).days
            
            if days_since_last_login == 1:
                self.login_streak += 1
            elif days_since_last_login > 1:
                self.login_streak = 1
        else:
            self.login_streak = 1
        
        self.last_login_date = today
        self.total_logins += 1
        self.save()

    def update_password_timestamp(self):
        self.password_updated_at = timezone.now()
        self.save()

    def get_password_strength(self):
        """Lógica simplificada para avaliar força da senha"""
        # Implemente sua lógica aqui ou remova se não for usada
        return "Forte"

    
        
    def get_profile_completion(self):
        """Calcular percentual de completude do perfil"""
        try:
            user = self.user
            completed_fields = 0
            total_fields = 4
            
            if user.first_name and user.first_name.strip(): 
                completed_fields += 1
            if user.last_name and user.last_name.strip(): 
                completed_fields += 1
            if user.email and user.email.strip(): 
                completed_fields += 1
            if self.foto_perfil and self.foto_perfil.name != 'default.jpg': 
                completed_fields += 1
            
            return int((completed_fields / total_fields) * 100)
        except Exception as e:
            return 0  # Retorna 0 em caso de erro
    


    def get_activity_display(self):
        """Retorna o nome amigável para o tipo de atividade"""
        activity_names = {
            'login': 'Login realizado',
            'password_change': 'Senha alterada',
            'profile_update': 'Perfil atualizado',
            'photo_change': 'Foto alterada',
        }
        return activity_names.get(self.activity_type, 'Atividade desconhecida')

    def get_description(self):
        """Retorna descrição detalhada da atividade"""
        descriptions = {
            'login': 'Acesso ao sistema',
            'password_change': 'Alteração de segurança',
            'profile_update': 'Informações pessoais',
            'photo_change': 'Foto de perfil',
        }
        return descriptions.get(self.activity_type, 'Atividade do usuário')


class UserActivity(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-data_criacao']
        verbose_name = 'Atividade do Usuário'
        verbose_name_plural = 'Atividades dos Usuários'
        indexes = [
            models.Index(fields=['user', 'data_criacao']),
        ]


class UserLogin(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-data_criacao']
        verbose_name = 'Login do Usuário'
        verbose_name_plural = 'Logins dos Usuários'
        indexes = [
            models.Index(fields=['user', 'data_criacao']),
        ]


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()