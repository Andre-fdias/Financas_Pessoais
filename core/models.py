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
        ('001', 'Banco do Brasil'),
        ('003', 'Banco da Amazônia'),
        ('004', 'Banco do Nordeste'),
        ('007', 'BNDES'),
        ('010', 'Credicoamo'),
        ('011', 'Credit Suisse Brasil'),
        ('012', 'Banco Inbursa'),
        ('014', 'Natixis Brasil'),
        ('015', 'UBS Brasil'),
        ('016', 'Coop. Créd. Desp. Trânsito'),
        ('017', 'BNY Mellon Brasil'),
        ('018', 'Banco Tricury'),
        ('021', 'Banestes'),
        ('024', 'Banco Bandepe'),
        ('025', 'Banco Alfa'),
        ('029', 'Itaú Consignado'),
        ('033', 'Santander Brasil'),
        ('036', 'Bradesco BBI'),
        ('037', 'Banco do Pará'),
        ('040', 'Banco Cargill'),
        ('041', 'Banrisul'),
        ('047', 'Banese'),
        ('060', 'Confidence Câmbio'),
        ('062', 'Hipercard Banco'),
        ('063', 'Bradescard'),
        ('064', 'Goldman Sachs Brasil'),
        ('065', 'Banco AndBank'),
        ('066', 'Morgan Stanley'),
        ('069', 'Banco Crefisa'),
        ('070', 'BRB'),
        ('074', 'Banco Safra'),
        ('075', 'ABN Amro Brasil'),
        ('076', 'Banco KDB Brasil'),
        ('077', 'Banco Inter'),
        ('078', 'Haitong Brasil'),
        ('079', 'Original Agronegócio'),
        ('080', 'BT Corretora'),
        ('081', 'Bancorbrás'),
        ('082', 'Banco Topázio'),
        ('083', 'Banco da China Brasil'),
        ('084', 'Uniprime Norte PR'),
        ('085', 'Ailos'),
        ('089', 'Cred. Rural Mogiana'),
        ('091', 'CCECM/RS'),
        ('092', 'BRK S.A.'),
        ('093', 'Pólocred'),
        ('094', 'Banco Finaxis'),
        ('095', 'Travelex'),
        ('096', 'Banco B3'),
        ('097', 'CCNB'),
        ('098', 'Credialiança'),
        ('099', 'Uniprime Central'),
        ('104', 'Caixa Econômica'),
        ('107', 'Banco Bocom BBM'),
        ('108', 'PortoCred'),
        ('111', 'Banco Oliveira Trust'),
        ('113', 'Magliano Corretora'),
        ('114', 'CCCE/ES'),
        ('117', 'Advanced Câmbio'),
        ('119', 'Western Union Brasil'),
        ('120', 'Banco Rodobens'),
        ('121', 'Banco Agibank'),
        ('122', 'Bradesco BERJ'),
        ('124', 'Woori Bank Brasil'),
        ('125', 'Brasil Plural'),
        ('126', 'BR Partners'),
        ('127', 'Codepe Câmbio'),
        ('128', 'MS Bank'),
        ('129', 'UBS Investimento'),
        ('130', 'Caruana S.A.'),
        ('131', 'Tullett Prebon'),
        ('132', 'ICBC Brasil'),
        ('133', 'Conf. Nac. Cooper. Centrais'),
        ('134', 'BGC Liquidez'),
        ('135', 'Gradual Corretora'),
        ('136', 'Unicred'),
        ('137', 'Multimoney Câmbio'),
        ('138', 'Get Money Câmbio'),
        ('139', 'Intesa Sanpaolo Brasil'),
        ('140', 'Easynvest'),
        ('142', 'Broker Brasil'),
        ('143', 'Treviso Câmbio'),
        ('144', 'Bexs Câmbio'),
        ('145', 'Levycam Corretora'),
        ('146', 'Guitta Câmbio'),
        ('149', 'Facta Financeira'),
        ('157', 'ICAP Brasil'),
        ('159', 'Casa do Crédito'),
        ('163', 'Commerzbank Brasil'),
        ('169', 'Banco Olé Bonsucesso'),
        ('173', 'BRL Trust'),
        ('174', 'Pernambucanas Financ.'),
        ('177', 'Guide Investimentos'),
        ('180', 'CM Capital Markets'),
        ('182', 'Dacasa Financeira'),
        ('183', 'Socred'),
        ('184', 'Itaú BBA'),
        ('188', 'Ativa Investimentos'),
        ('189', 'HS Financeira'),
        ('190', 'Servicoop'),
        ('191', 'Nova Futura'),
        ('194', 'Parmetal'),
        ('196', 'Fair Câmbio'),
        ('197', 'Stone Pagamentos'),
        ('204', 'Bradesco Cartões'),
        ('208', 'BTG Pactual'),
        ('212', 'Banco Original'),
        ('213', 'Banco Arbi'),
        ('217', 'John Deere'),
        ('218', 'Banco BS2'),
        ('222', 'Credit Agrícole Brasil'),
        ('224', 'Banco Fibra'),
        ('233', 'Banco Cifra'),
        ('237', 'Bradesco'),
        ('241', 'Banco Classico'),
        ('243', 'Banco Máxima'),
        ('246', 'ABC Brasil'),
        ('249', 'Investcred Unibanco'),
        ('250', 'BCV'),
        ('253', 'Bexs Corretora'),
        ('254', 'Paraná Banco'),
        ('259', 'Banco Modal'),
        ('260', 'Nubank'),
        ('265', 'Banco Fator'),
        ('266', 'Banco Cédula'),
        ('268', 'Barigui'),
        ('269', 'HSBC Investimento'),
        ('270', 'Sagitur Câmbio'),
        ('271', 'IB Corretora'),
        ('272', 'AGK Câmbio'),
        ('273', 'CCR São Miguel Oeste'),
        ('274', 'Money Plus'),
        ('276', 'Senff'),
        ('278', 'Genial Investimentos'),
        ('279', 'CCR Primavera do Leste'),
        ('280', 'Avista'),
        ('281', 'Coopavel'),
        ('283', 'RB Capital'),
        ('285', 'Frente Câmbio'),
        ('286', 'CCR Ouro Sul'),
        ('288', 'Carol DTVM'),
        ('289', 'EFX Câmbio'),
        ('290', 'Pago Seguro'),
        ('292', 'BS2 DTVM'),
        ('293', 'Lastro RDV'),
        ('296', 'Vision Câmbio'),
        ('298', 'Vips Câmbio'),
        ('299', 'Sorocred'),
        ('300', 'Banco Nacion Argentina'),
        ('301', 'BPP IP'),
        ('306', 'Portopar DTVM'),
        ('307', 'Terra Investimentos'),
        ('309', 'CAMBIONET'),
        ('310', 'VORTX DTVM'),
        ('311', 'Dourada Câmbio'),
        ('312', 'HSCM'),
        ('313', 'Amazônia Câmbio'),
        ('315', 'PI DTVM'),
        ('318', 'Banco BMG'),
        ('319', 'OM DTVM'),
        ('320', 'China Construction Bank'),
        ('321', 'Crefaz'),
        ('322', 'CCR Abelardo Luz'),
        ('323', 'Mercado Pago'),
        ('324', 'Cartos'),
        ('325', 'Órama DTVM'),
        ('326', 'Parati'),
        ('329', 'Qi Sociedade'),
        ('330', 'Banco Bari'),
        ('331', 'Fram Capital'),
        ('332', 'Acesso Pagamentos'),
        ('335', 'Banco Digio'),
        ('336', 'C6 Bank'),
        ('340', 'Super Pagamentos'),
        ('341', 'Itaú'),
        ('342', 'Creditas'),
        ('343', 'FFA'),
        ('348', 'XP Investimentos'),
        ('349', 'AL5'),
        ('350', 'CCR Peq. Agricultores'),
        ('352', 'Torra Corretora'),
        ('354', 'Necton Investimentos'),
        ('355', 'Ótimo'),
        ('358', 'Mercantil do Brasil'),
        ('359', 'Zema'),
        ('360', 'Trinus Capital'),
        ('362', 'Cielo'),
        ('363', 'Singulare'),
        ('364', 'Gerencianet'),
        ('365', 'Solidus'),
        ('366', 'Societe Generale'),
        ('367', 'Vitreo DTVM'),
        ('368', 'Banco CSF'),
        ('370', 'Mizuho Brasil'),
        ('371', 'Warren'),
        ('373', 'UP.P'),
        ('374', 'Realize'),
        ('376', 'JP Morgan'),
        ('377', 'MS Sociedade'),
        ('378', 'BBC'),
        ('379', 'Cooperforte'),
        ('380', 'PicPay'),
        ('381', 'Mercedes-Benz'),
        ('382', 'Fidúcia'),
        ('383', 'BoletoBancário'),
        ('384', 'Global Finanças'),
        ('385', 'CCR Ibiam'),
        ('386', 'Nu Financeira'),
        ('387', 'Toyota Brasil'),
        ('388', 'Original Agronegócio'),
        ('389', 'Mercantil Brasil'),
        ('390', 'GM'),
        ('391', 'CCR Palmitos'),
        ('392', 'Volkswagen'),
        ('393', 'Honda'),
        ('394', 'Bradesco Financiamentos'),
        ('395', 'CCR Ouro'),
        ('396', 'Hub Pagamentos'),
        ('397', 'Listo'),
        ('398', 'Ideal Corretora'),
        ('399', 'Kirton Bank'),
        ('626', 'C6 Consignado'),
        ('630', 'Letsbank'),
        ('633', 'Rendimento'),
        ('634', 'Triângulo'),
        ('637', 'Sofisa'),
        ('643', 'Pine'),
        ('652', 'Itaú Holding'),
        ('653', 'Voiter'),
        ('654', 'Digimais'),
        ('655', 'Votorantim'),
        ('707', 'Daycoval'),
        ('712', 'Ourinvest'),
        ('739', 'Cetelem'),
        ('741', 'Ribeirão Preto'),
        ('743', 'Semear'),
        ('745', 'Citibank'),
        ('746', 'Modal'),
        ('747', 'Rabobank'),
        ('748', 'Sicredi'),
        ('751', 'Scotiabank'),
        ('752', 'BNP Paribas'),
        ('753', 'Novo Banco Continental'),
        ('754', 'Banco Sistema'),
        ('755', 'Bank of America'),
        ('756', 'Sicoob'),
        ('757', 'KEB Hana Brasil'),
    ],
    
    "Cartoes de Credito": [
        ('VISA', 'Visa'),
        ('MASTERCARD', 'Mastercard'),
        ('AMEX', 'American Express'),
        ('ELO', 'Elo'),
        ('HIPERCARD', 'Hipercard'),
        ('DINERS', 'Diners Club'),
        ('DISCOVER', 'Discover'),
        ('JCB', 'JCB'),
        ('AURA', 'Aura'),
        ('CABAL', 'Cabal'),
        ('BANESCARD', 'Banescard'),
        ('CREDSYSTEM', 'Credsystem'),
        ('CREDZ', 'Credz'),
        ('FORTBRASIL', 'FortBrasil'),
        ('GRENCARD', 'Grencard'),
        ('PERSONALCARD', 'PersonalCard'),
        ('POLICARD', 'Policard'),
        ('SOROCRED', 'Sorocred'),
        ('VEROCHEQUE', 'Verocheque'),
        ('CREDISHOP', 'Credishop'),
        ('AGICARD', 'Agicard'),
        ('AVISTA', 'Avista'),
        ('CARDOBOM', 'Cardobom'),
        ('UPBRASIL', 'UpBrasil'),
        ('BIGCARD', 'BigCard'),
    ],
    
    "Cartoes de Alimentacao": [
        ('VALECARD', 'Valecard'),
        ('RAIO', 'Raio'),
        ('ALELO', 'Alelo'),
        ('SODEXO', 'Sodexo'),
        ('TICKET', 'Ticket'),
        ('VR', 'VR'),
        ('BANESCARD', 'Banescard'),
        ('GREENCARD', 'Green Card'),
        ('UP', 'UP'),
        ('PLURECARD', 'Plurecard'),
        ('VEROCARD', 'Verocard'),
        ('CABAL', 'Cabal'),
        ('GOODCARD', 'Goodcard'),
        ('FLEX', 'Flex'),
        ('SUPERCARD', 'Supercard'),
        ('FACILCARD', 'Facilcard'),
        ('PERSONALCARD', 'PersonalCard'),
        ('NUTRICASH', 'Nutricash'),
        ('MAISCARD', 'Maiscard'),
        ('FESTACARD', 'Festacard'),
        ('QUALICARD', 'Qualicard'),
        ('PESCARD', 'Pescard'),
        ('SOCIALCARD', 'Socialcard'),
        ('REFEICARD', 'Refeicard'),
        ('HORTIFRUTI', 'Hortifruti'),
        ('ACOUGUE', 'Açougue'),
        ('FEIRA', 'Feira'),
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

    proprietario = models.ForeignKey(User, on_delete=models.CASCADE)
    nome_banco = models.CharField(max_length=20, choices=BANCO_CHOICES)
    tipo = models.CharField(max_length=20, choices=TIPO_CONTA_CHOICES)
    agencia = models.CharField(max_length=10, blank=True, null=True)
    numero_conta = models.CharField(max_length=20, blank=True, null=True)
    saldo_atual = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    ativa = models.BooleanField(default=True)
    
    # Campos específicos para cartão de crédito
    numero_cartao = models.CharField(max_length=20, blank=True, null=True)
    limite_cartao = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    dia_fechamento_fatura = models.PositiveSmallIntegerField(blank=True, null=True)
    dia_vencimento_fatura = models.PositiveSmallIntegerField(blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = 'Conta Bancária'
        verbose_name_plural = 'Contas Bancárias'
        ordering = ['-data_criacao']

    def __str__(self):
        # Retorna o nome da instituição financeira e o número da conta/cartão
        display_name = self.get_nome_banco_display()
        if self.tipo in ['credito', 'debito', 'alimentacao']:
            return f"{display_name} - {self.numero_conta}"
        return f"{display_name} - {self.agencia}/{self.numero_conta}"
    
    def saldo_formatado(self):
        return f"R$ {self.saldo_atual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    def is_cartao_credito(self):
        return self.tipo == 'cartao_credito'

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