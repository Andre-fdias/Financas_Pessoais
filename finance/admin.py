from django.contrib import admin
from .models import BankAccount, CreditCard, Transaction, Budget

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('bank', 'account_type', 'agency', 'account_number', 'owner', 'is_active')
    list_filter = ('bank', 'account_type', 'is_active')
    search_fields = ('agency', 'account_number', 'owner')
    ordering = ('bank', 'account_type')

@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    list_display = ('card_name', 'card_flag', 'card_number', 'owner', 'limit', 'is_active')
    list_filter = ('card_flag', 'is_active')
    search_fields = ('card_name', 'card_number', 'owner')
    ordering = ('card_flag', 'card_name')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'transaction_type', 'amount', 'description', 'category', 'is_recurrent')
    list_filter = ('transaction_type', 'category', 'is_recurrent', 'payment_method')
    search_fields = ('description', 'notes')
    date_hierarchy = 'date'
    ordering = ('-date',)

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'period', 'start_date', 'end_date')
    list_filter = ('category', 'period')
    search_fields = ('notes',)
    date_hierarchy = 'start_date'