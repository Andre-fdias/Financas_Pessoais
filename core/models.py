from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from decimal import Decimal
from datetime import datetime

# CHOICES (Idealmente, mova para um arquivo core/choices.py)

PERIODICIDADE_CHOICES = [
    ('unica', 'Única'),
    ('diaria', 'Diária'),
    ('semanal', 'Semanal'),
    ('mensal', 'Mensal'),
    ('anual', 'Anual'),
]

# Nova estrutura de instituições financeiras
INSTITUICOES_FINANCEIRAS = {
    "Bancos": [
        ('001', 'Banco do Brasil S.A.'),
        ('033', 'Banco Santander (Brasil) S.A.'),
        ('104', 'Caixa Econômica Federal'),
        ('237', 'Banco Bradesco S.A.'),
        ('260', 'Nu Pagamentos S.A. (Nubank)'),
        ('323', 'Mercado Pago - Banco MercadoPago de Pagamentos S.A.'),
        ('336', 'Banco C6 S.A. (C6 Bank)'),
        ('341', 'Itaú Unibanco S.A.'),
        ('380', 'PicPay Bank S.A.'),
        ('077', 'Banco Inter S.A.'),
        ('655', 'Banco Votorantim S.A. (Neon)'),
        ('212', 'Banco Original S.A.'),
        ('746', 'Banco Modal S.A.'),
        ('623', 'Banco Pan S.A.'),
        ('069', 'Banco Crefisa S.A.'),
        ('070', 'Banco de Brasília S.A. (BRB)'),
        ('748', 'Banco Cooperativo Sicredi S.A.'),
        ('756', 'Banco Cooperativo do Brasil S.A. (Sicoob)'),
    ],
    
    "Cartoes de Credito": [
        ('VISA', 'Visa'),
        ('MASTERCARD', 'Mastercard'),
        ('AMEX', 'American Express'),
        ('ELO', 'Elo'),
        ('HIPERCARD', 'Hipercard'),
        ('DINERS', 'Diners Club International'),
        ('DISCOVER', 'Discover'),
        ('JCB', 'JCB (Japan Credit Bureau)'),
    ],
    
    "Cartoes de Alimentacao": [
        ('VALECARD', 'Valecard'),
        ('ALELO', 'Alelo'),
        ('SODEXO', 'Sodexo'),
        ('TICKET', 'Ticket (Edenred)'),
        ('VR', 'VR Benefícios'),
        ('BANESCARD', 'Banescard Alimentação'),
        ('GREENCARD', 'Green Card'),
    ]
}

# Unifica todas as escolhas de instituições financeiras em uma única lista para BANCO_CHOICES
BANCO_CHOICES = []
for category_choices in INSTITUICOES_FINANCEIRAS.values():
    BANCO_CHOICES.extend(category_choices)


FORMA_RECEBIMENTO_CHOICES = [
    ('dinheiro', 'Dinheiro (Caixa)'),
    ('pix', 'PIX'),
    ('ted_doc', 'TED/DOC'),
    ('cartao', 'Cartão (Crédito/Débito)'),
    ('boleto', 'Boleto'),
    ('outros', 'Outros'),
]

FORMA_PAGAMENTO_CHOICES = [
    ('dinheiro', 'Dinheiro'),
    ('cartao_credito', 'Cartão de Crédito'),
    ('cartao_debito', 'Cartão de Débito'),
    ('pix', 'PIX'),
    ('boleto', 'Boleto'),
    ('cheque', 'Cheque'),
    ('outros', 'Outros'),
]

TIPO_PAGAMENTO_DETALHE_CHOICES = [
    ('avista', 'À vista'),
    ('parcelado', 'Parcelado'),
]

SITUACAO_CHOICES = [
    ('pago', 'Pago'),
    ('pendente', 'Pendente'),
]


# MODELS

class ContaBancaria(models.Model):
    """
    Representa uma conta bancária ou cartão associado a um usuário.
    Pode ser uma conta corrente, poupança, cartão de crédito, etc.
    """
    TIPO_CONTA_CHOICES = [
        ('corrente', 'Conta Corrente'),
        ('poupanca', 'Conta Poupança'),
        ('credito', 'Cartão de Crédito'),
        ('debito', 'Cartão de Débito'),
        ('alimentacao', 'Cartão Alimentação'),
    ]

    proprietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contas_proprietario')
    nome_banco = models.CharField(max_length=100, choices=BANCO_CHOICES)
    agencia = models.CharField(max_length=20, blank=True, null=True)  # Permite nulo
    numero_conta = models.CharField(max_length=20, blank=True, null=True)  # Permite nulo
    tipo = models.CharField(max_length=20, choices=TIPO_CONTA_CHOICES, default='corrente')
    ativa = models.BooleanField(default=True)

    def __str__(self):
        # Retorna o nome da instituição financeira e o número da conta/cartão
        display_name = self.get_nome_banco_display()
        if self.tipo in ['credito', 'debito', 'alimentacao']:
            return f"{display_name} - {self.numero_conta}"
        return f"{display_name} - {self.agencia}/{self.numero_conta}"

    def clean(self):
        super().clean()
        if self.tipo in ['corrente', 'poupanca']:
            if not self.agencia:
                raise ValidationError({'agencia': 'Agência é obrigatória para contas correntes e poupança.'})
            if not self.numero_conta:
                raise ValidationError({'numero_conta': 'Número da conta é obrigatório para contas correntes e poupança.'})
        elif self.agencia:
            raise ValidationError({'agencia': 'Agência não é aplicável para este tipo de conta.'})


class Categoria(models.Model):
    """
    Representa uma categoria de transação (Entrada ou Saída) criada pelo usuário.
    Ex: Moradia, Alimentação, Salário.
    """
    nome = models.CharField(max_length=100) # Remover unique=True para permitir nomes repetidos por usuários diferentes
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        unique_together = ('nome', 'usuario') # Garante unicidade por usuário

    def __str__(self):
        return self.nome


class Subcategoria(models.Model):
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
        unique_together = ('nome', 'categoria', 'usuario') # Garante unicidade por categoria e usuário

    def __str__(self):
        return f"{self.nome} ({self.categoria.nome})"


from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Entrada(models.Model):
    FORMA_RECEBIMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro (Caixa)'),
        ('pix', 'PIX'),
        ('ted_doc', 'TED/DOC'),
        ('cartao', 'Cartão (Crédito/Débito)'),
        ('boleto', 'Boleto'),
        ('outros', 'Outros'),
    ]

    # Campos principais
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='entradas',
        verbose_name="Usuário"
    )
    conta_bancaria = models.ForeignKey(
        'ContaBancaria', 
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
    
    # Campos automáticos
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atualização"
    )

    class Meta:
        verbose_name = "Entrada"
        verbose_name_plural = "Entradas"
        ordering = ['-data', '-data_criacao']

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

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

# Choices
CATEGORIA_CHOICES = [
    ('moradia', 'Moradia'),
    ('alimentacao', 'Alimentação'),
    ('transporte', 'Transporte'),
    ('saude', 'Saúde'),
    ('educacao', 'Educação'),
    ('lazer', 'Lazer'),
    ('seguros', 'Seguros'),
    ('pessoais', 'Despesas Pessoais'),
    ('familia', 'Família'),
    ('contas', 'Contas e Serviços'),
    ('investimentos', 'Investimentos'),
    ('impostos', 'Impostos'),
]

SUBCATEGORIA_CHOICES = [
    # Moradia
    ('moradia_aluguel', 'Aluguel', 'moradia'),
    ('moradia_financiamento', 'Financiamento Imobiliário', 'moradia'),
    ('moradia_condominio', 'Condomínio', 'moradia'),
    ('moradia_iptu', 'IPTU', 'moradia'),
    ('moradia_energia', 'Energia Elétrica', 'moradia'),
    ('moradia_agua', 'Água e Esgoto', 'moradia'),
    ('moradia_gas', 'Gás', 'moradia'),
    ('moradia_internet', 'Internet', 'moradia'),
    ('moradia_manutencao', 'Manutenção/Reparos', 'moradia'),

    # Alimentação
    ('alimentacao_supermercado', 'Supermercado', 'alimentacao'),
    ('alimentacao_hortifruti', 'Hortifruti', 'alimentacao'),
    ('alimentacao_padaria', 'Padaria', 'alimentacao'),
    ('alimentacao_restaurante', 'Restaurante', 'alimentacao'),
    ('alimentacao_lanches', 'Lanches', 'alimentacao'),
    
    # Transporte
    ('transporte_combustivel', 'Combustível', 'transporte'),
    ('transporte_manutencao', 'Manutenção Veicular', 'transporte'),
    ('transporte_seguro', 'Seguro Veicular', 'transporte'),
    ('transporte_estacionamento', 'Estacionamento', 'transporte'),
    ('transporte_publico', 'Transporte Público', 'transporte'),
    ('transporte_app', 'Táxi/App de Transporte', 'transporte'),
    
    # Saúde
    ('saude_plano', 'Plano de Saúde', 'saude'),
    ('saude_medicamentos', 'Medicamentos', 'saude'),
    ('saude_consultas', 'Consultas Médicas', 'saude'),
    ('saude_exames', 'Exames', 'saude'),
    ('saude_odontologia', 'Odontologia', 'saude'),
    
    # Educação
    ('educacao_mensalidade', 'Mensalidade Escolar/Faculdade', 'educacao'),
    ('educacao_cursos', 'Cursos/Treinamentos', 'educacao'),
    ('educacao_materiais', 'Livros/Material Didático', 'educacao'),
    
    # Lazer
    ('lazer_cinema', 'Cinema/Teatro', 'lazer'),
    ('lazer_shows', 'Shows/Eventos', 'lazer'),
    ('lazer_viagens', 'Viagens', 'lazer'),
    ('lazer_entretenimento', 'Salão de Jogos/Entretenimento', 'lazer'),

    # Seguros
    ('seguros_vida', 'Seguro de Vida', 'seguros'),
    ('seguros_residencial', 'Seguro Residencial', 'seguros'),
    ('seguros_viagem', 'Seguro Viagem', 'seguros'),

    # Despesas Pessoais
    ('pessoais_academia', 'Academia/Atividade Física', 'pessoais'),
    ('pessoais_estetica', 'Estética/Beleza', 'pessoais'),
    ('pessoais_vestuario', 'Vestuário', 'pessoais'),
    ('pessoais_calcados', 'Calçados', 'pessoais'),
    ('pessoais_acessorios', 'Acessórios', 'pessoais'),

    # Família
    ('familia_mesada', 'Mesada para Filhos', 'familia'),
    ('familia_presentes', 'Presentes', 'familia'),
    ('familia_pets', 'Cuidados com Pets', 'familia'),

    # Contas e Serviços
    ('contas_telefone', 'Telefone', 'contas'),
    ('contas_assinaturas', 'Assinaturas', 'contas'),
    ('contas_tv', 'TV por Assinatura/Streaming', 'contas'),

    # Investimentos
    ('investimentos_poupanca', 'Poupança', 'investimentos'),
    ('investimentos_fundos', 'Fundos de Investimento', 'investimentos'),
    ('investimentos_acoes', 'Ações', 'investimentos'),
    ('investimentos_cripto', 'Criptomoedas', 'investimentos'),

    # Impostos
    ('impostos_irpf', 'IRPF', 'impostos'),
    ('impostos_inss', 'INSS', 'impostos'),
    ('impostos_taxas', 'Taxas/Tributos', 'impostos'),
]

FORMA_PAGAMENTO_CHOICES = [
    ('dinheiro', 'Dinheiro'),
    ('cartao_credito', 'Cartão de Crédito'),
    ('cartao_debito', 'Cartão de Débito'),
    ('pix', 'PIX'),
    ('boleto', 'Boleto'),
    ('cheque', 'Cheque'),
    ('outros', 'Outros'),
]

TIPO_PAGAMENTO_DETALHE_CHOICES = [
    ('avista', 'À vista'),
    ('parcelado', 'Parcelado'),
]

SITUACAO_CHOICES = [
    ('pago', 'Pago'),
    ('pendente', 'Pendente'),
]

PERIODICIDADE_CHOICES = [
    ('unica', 'Única'),
    ('diaria', 'Diária'),
    ('semanal', 'Semanal'),
    ('mensal', 'Mensal'),
    ('anual', 'Anual'),
]

class Saida(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    conta_bancaria = models.ForeignKey('ContaBancaria', on_delete=models.CASCADE)
    nome = models.CharField(max_length=255, verbose_name="Nome da Transação")
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    data_lancamento = models.DateField(default=timezone.now, verbose_name="Data de Lançamento")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    local = models.CharField(max_length=100, blank=True, null=True, verbose_name="Local")
    
    categoria = models.CharField(
        max_length=20,
        choices=[(c[0], c[1]) for c in CATEGORIA_CHOICES],
        verbose_name="Categoria"
    )
    
    subcategoria = models.CharField(
        max_length=30,
        choices=[(sc[0], sc[1]) for sc in SUBCATEGORIA_CHOICES],
        blank=True,
        null=True,
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
        default='pendente', blank=True, null=True,
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
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta: 
        ordering = ['-data_lancamento']
        verbose_name = "Saída"
        verbose_name_plural = "Saídas"

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