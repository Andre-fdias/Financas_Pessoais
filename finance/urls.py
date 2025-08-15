from django.urls import path
from finance import views

app_name = 'finance'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Contas bancárias
    path('accounts/', views.bank_account_list, name='bank_account_list'),
    path('accounts/new/', views.bank_account_create, name='bank_account_create'),
    path('accounts/<int:pk>/edit/', views.bank_account_edit, name='bank_account_edit'),
    path('accounts/<int:pk>/delete/', views.bank_account_delete, name='bank_account_delete'),
    
    # Cartões de crédito
    path('cards/', views.credit_card_list, name='credit_card_list'),
    path('cards/new/', views.credit_card_create, name='credit_card_create'),
    path('cards/<int:pk>/edit/', views.credit_card_edit, name='credit_card_edit'),
    path('cards/<int:pk>/delete/', views.credit_card_delete, name='credit_card_delete'),
    
    # Transações
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/new/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    
    # Orçamentos
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/new/', views.budget_create, name='budget_create'),
    path('budgets/<int:pk>/edit/', views.budget_edit, name='budget_edit'),
    path('budgets/<int:pk>/delete/', views.budget_delete, name='budget_delete'),
    
    # Relatórios
    path('reports/', views.reports, name='reports'),
    path('forecast/', views.forecast, name='forecast'),
    
    # AJAX
    path('api/account/<int:account_id>/balance/', views.get_account_balance, name='get_account_balance'),
    path('api/card/<int:card_id>/balance/', views.get_card_balance, name='get_card_balance'),
]