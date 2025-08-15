from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta

# Bancos do Brasil (lista simplificada)
BANK_CHOICES = [
    ('001', 'Banco do Brasil'),
    ('033', 'Santander'),
    ('237', 'Bradesco'),
    ('341', 'Itaú'),
    ('104', 'Caixa Econômica Federal'),
    ('260', 'Nubank'),
    ('336', 'C6 Bank'),
    ('422', 'Banco Safra'),
    ('655', 'Banco Votorantim'),
    ('041', 'Banrisul'),
    ('077', 'Banco Inter'),
    ('212', 'Banco Original'),
    ('070', 'BRB'),
    ('735', 'Neon'),
    ('739', 'Banco Cetelem'),
    ('743', 'Banco Semear'),
    ('745', 'Citibank'),
    ('746', 'Banco Modal'),
    ('747', 'Banco Rabobank'),
    ('748', 'Sicredi'),
    ('751', 'Scotiabank'),
    ('752', 'Banco BNP Paribas'),
    ('753', 'Novo Banco Continental'),
    ('754', 'Banco Sistema'),
    ('755', 'Bank of America'),
    ('756', 'Banco Cooperativo do Brasil'),
]

ACCOUNT_TYPE_CHOICES = [
    ('CC', 'Conta Corrente'),
    ('PP', 'Poupança'),
    ('AP', 'Rendimentos de Aplicações'),
]

CARD_FLAG_CHOICES = [
    ('VISA', 'Visa'),
    ('MC', 'MasterCard'),
    ('ELO', 'Elo'),
    ('AMEX', 'American Express'),
    ('DINERS', 'Diners Club'),
    ('HIPER', 'Hipercard'),
    ('VR', 'Vale Refeição'),
    ('VA', 'Vale Alimentação'),
    ('SODEXO', 'Sodexo'),
    ('TICKET', 'Ticket'),
]

TRANSACTION_TYPE_CHOICES = [
    ('IN', 'Entrada'),
    ('OUT', 'Saída'),
]

EXPENSE_CATEGORY_CHOICES = [
    ('FOOD', 'Alimentação'),
    ('TRANSPORT', 'Transporte'),
    ('HOUSING', 'Moradia'),
    ('HEALTH', 'Saúde'),
    ('EDUCATION', 'Educação'),
    ('LEISURE', 'Lazer'),
    ('SHOPPING', 'Compras'),
    ('SERVICES', 'Serviços'),
    ('OTHERS', 'Outros'),
]

PAYMENT_METHOD_CHOICES = [
    ('CASH', 'À vista'),
    ('CREDIT', 'Crédito'),
    ('DEBIT', 'Débito'),
    ('PIX', 'PIX'),
    ('TRANSFER', 'Transferência'),
    ('OTHER', 'Outro'),
]

RECURRENCE_CHOICES = [
    ('NONE', 'Nenhuma'),
    ('DAILY', 'Diária'),
    ('WEEKLY', 'Semanal'),
    ('BIWEEKLY', 'Quinzenal'),
    ('MONTHLY', 'Mensal'),
    ('BIMONTHLY', 'Bimestral'),
    ('QUARTERLY', 'Trimestral'),
    ('SEMIANNUAL', 'Semestral'),
    ('ANNUAL', 'Anual'),
]

class BankAccount(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bank = models.CharField(max_length=5, choices=BANK_CHOICES)
    account_type = models.CharField(max_length=2, choices=ACCOUNT_TYPE_CHOICES)
    agency = models.CharField(max_length=10)
    account_number = models.CharField(max_length=20)
    owner = models.CharField(max_length=100)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    opening_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_bank_display()} - {self.get_account_type_display()} {self.agency}/{self.account_number}"

    def current_balance(self):
        deposits = Transaction.objects.filter(
            account=self, 
            transaction_type='IN'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        withdrawals = Transaction.objects.filter(
            account=self, 
            transaction_type='OUT'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        return self.opening_balance + deposits - withdrawals

    class Meta:
        ordering = ['bank', 'account_type']
        unique_together = ['bank', 'agency', 'account_number']


class CreditCard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    card_name = models.CharField(max_length=100)
    card_flag = models.CharField(max_length=10, choices=CARD_FLAG_CHOICES)
    card_number = models.CharField(max_length=4)  # Últimos 4 dígitos
    owner = models.CharField(max_length=100)
    limit = models.DecimalField(max_digits=12, decimal_places=2)
    due_day = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(31)])
    closing_day = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(31)])
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_card_flag_display()} - {self.card_name} ****{self.card_number}"

    def current_balance(self):
        expenses = Transaction.objects.filter(
            credit_card=self,
            transaction_type='OUT'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        payments = Transaction.objects.filter(
            credit_card=self,
            transaction_type='IN',
            description__icontains='pagamento cartão'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        return expenses - payments

    def available_limit(self):
        return self.limit - self.current_balance()

    class Meta:
        ordering = ['card_flag', 'card_name']


class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORY_CHOICES, blank=True, null=True)
    subcategory = models.CharField(max_length=50, blank=True, null=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    is_recurrent = models.BooleanField(default=False)
    recurrence = models.CharField(max_length=15, choices=RECURRENCE_CHOICES, default='NONE')
    installments = models.PositiveIntegerField(default=1)
    current_installment = models.PositiveIntegerField(default=1)
    account = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, blank=True, null=True)
    credit_card = models.ForeignKey(CreditCard, on_delete=models.SET_NULL, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.description} - R${self.amount}"

    def save(self, *args, **kwargs):
        # Se for uma transação parcelada, criar as próximas parcelas
        if self.installments > 1 and self.current_installment == 1:
            self._create_installments()
        super().save(*args, **kwargs)

    def _create_installments(self):
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        for i in range(2, self.installments + 1):
            next_date = self.date + relativedelta(months=i-1)
            Transaction.objects.create(
                user=self.user,
                transaction_type=self.transaction_type,
                amount=self.amount,
                date=next_date,
                description=f"{self.description} ({i}/{self.installments})",
                category=self.category,
                subcategory=self.subcategory,
                payment_method=self.payment_method,
                is_recurrent=self.is_recurrent,
                recurrence=self.recurrence,
                installments=self.installments,
                current_installment=i,
                account=self.account,
                credit_card=self.credit_card,
                location=self.location,
                notes=self.notes
            )

    class Meta:
        ordering = ['-date', '-created_at']


class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    period = models.CharField(max_length=10, choices=[('MONTHLY', 'Mensal'), ('YEARLY', 'Anual')])
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_category_display()} - R${self.amount} ({self.get_period_display()})"

    def spent_amount(self):
        transactions = Transaction.objects.filter(
            user=self.user,
            transaction_type='OUT',
            category=self.category,
            date__gte=self.start_date,
            date__lte=self.end_date if self.end_date else timezone.now().date()
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        return transactions

    def remaining_amount(self):
        return self.amount - self.spent_amount()

    def percentage_spent(self):
        if self.amount == 0:
            return 0
        return (self.spent_amount() / self.amount) * 100

    class Meta:
        ordering = ['category']