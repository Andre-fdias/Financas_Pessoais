from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json

from .models import BankAccount, CreditCard, Transaction, Budget
from .forms import BankAccountForm, CreditCardForm, TransactionForm, BudgetForm, TransactionFilterForm


@login_required
def dashboard(request):
    # Saldo total
    accounts = BankAccount.objects.filter(user=request.user, is_active=True)
    total_balance = sum(account.current_balance() for account in accounts)
    
    # Cartões de crédito
    credit_cards = CreditCard.objects.filter(user=request.user, is_active=True)
    total_credit_limit = sum(card.limit for card in credit_cards)
    total_credit_used = sum(card.current_balance() for card in credit_cards)
    
    # Últimas transações
    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:10]
    
    # Gastos por categoria (últimos 30 dias)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    expenses_by_category = (
        Transaction.objects
        .filter(user=request.user, transaction_type='OUT', date__gte=thirty_days_ago)
        .values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    
    # Orçamentos
    budgets = Budget.objects.filter(user=request.user)
    
    context = {
        'total_balance': total_balance,
        'accounts': accounts,
        'credit_cards': credit_cards,
        'total_credit_limit': total_credit_limit,
        'total_credit_used': total_credit_used,
        'recent_transactions': recent_transactions,
        'expenses_by_category': expenses_by_category,
        'budgets': budgets,
    }
    
    return render(request, 'finance/dashboard.html', context)


@login_required
def bank_account_list(request):
    accounts = BankAccount.objects.filter(user=request.user).order_by('bank', 'account_type')
    return render(request, 'finance/accounts/list.html', {'accounts': accounts})


@login_required
def bank_account_create(request):
    if request.method == 'POST':
        form = BankAccountForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conta bancária criada com sucesso!')
            return redirect('bank_account_list')
    else:
        form = BankAccountForm(user=request.user)
    
    return render(request, 'finance/accounts/form.html', {'form': form, 'title': 'Nova Conta Bancária'})


@login_required
def bank_account_edit(request, pk):
    account = get_object_or_404(BankAccount, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = BankAccountForm(request.POST, instance=account, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conta bancária atualizada com sucesso!')
            return redirect('bank_account_list')
    else:
        form = BankAccountForm(instance=account, user=request.user)
    
    return render(request, 'finance/accounts/form.html', {'form': form, 'title': 'Editar Conta Bancária'})


@login_required
def bank_account_delete(request, pk):
    account = get_object_or_404(BankAccount, pk=pk, user=request.user)
    
    if request.method == 'POST':
        account.delete()
        messages.success(request, 'Conta bancária excluída com sucesso!')
        return redirect('bank_account_list')
    
    return render(request, 'finance/accounts/delete.html', {'account': account})


@login_required
def credit_card_list(request):
    cards = CreditCard.objects.filter(user=request.user).order_by('card_flag', 'card_name')
    return render(request, 'finance/cards/list.html', {'cards': cards})


@login_required
def credit_card_create(request):
    if request.method == 'POST':
        form = CreditCardForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cartão de crédito criado com sucesso!')
            return redirect('credit_card_list')
    else:
        form = CreditCardForm(user=request.user)
    
    return render(request, 'finance/cards/form.html', {'form': form, 'title': 'Novo Cartão de Crédito'})


@login_required
def credit_card_edit(request, pk):
    card = get_object_or_404(CreditCard, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = CreditCardForm(request.POST, instance=card, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cartão de crédito atualizado com sucesso!')
            return redirect('credit_card_list')
    else:
        form = CreditCardForm(instance=card, user=request.user)
    
    return render(request, 'finance/cards/form.html', {'form': form, 'title': 'Editar Cartão de Crédito'})


@login_required
def credit_card_delete(request, pk):
    card = get_object_or_404(CreditCard, pk=pk, user=request.user)
    
    if request.method == 'POST':
        card.delete()
        messages.success(request, 'Cartão de crédito excluído com sucesso!')
        return redirect('credit_card_list')
    
    return render(request, 'finance/cards/delete.html', {'card': card})


@login_required
def transaction_list(request):
    form = TransactionFilterForm(request.GET or None, user=request.user)
    transactions = Transaction.objects.filter(user=request.user).order_by('-date', '-created_at')
    
    if form.is_valid():
        data = form.cleaned_data
        
        if data.get('start_date'):
            transactions = transactions.filter(date__gte=data['start_date'])
        
        if data.get('end_date'):
            transactions = transactions.filter(date__lte=data['end_date'])
        
        if data.get('transaction_type'):
            transactions = transactions.filter(transaction_type=data['transaction_type'])
        
        if data.get('category'):
            transactions = transactions.filter(category=data['category'])
        
        if data.get('account'):
            transactions = transactions.filter(account=data['account'])
        
        if data.get('credit_card'):
            transactions = transactions.filter(credit_card=data['credit_card'])
        
        if data.get('payment_method'):
            transactions = transactions.filter(payment_method=data['payment_method'])
        
        if data.get('is_recurrent'):
            transactions = transactions.filter(is_recurrent=True)
    
    # Exportar para Excel
    if 'export' in request.GET:
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="extrato_financeiro.xls"'
        
        # Crie uma planilha Excel simples (usando html como uma solução rápida)
        html = render_to_string('finance/transactions/export.html', {
            'transactions': transactions,
            'filter': form.cleaned_data
        })
        response.write(html)
        return response
    
    context = {
        'transactions': transactions,
        'form': form,
    }
    return render(request, 'finance/transactions/list.html', context)


@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save()
            messages.success(request, 'Transação registrada com sucesso!')
            
            if 'save_and_new' in request.POST:
                return redirect('transaction_create')
            return redirect('transaction_list')
    else:
        form = TransactionForm(user=request.user)
    
    return render(request, 'finance/transactions/form.html', {'form': form, 'title': 'Nova Transação'})


@login_required
def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transação atualizada com sucesso!')
            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    
    return render(request, 'finance/transactions/form.html', {'form': form, 'title': 'Editar Transação'})


@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transação excluída com sucesso!')
        return redirect('transaction_list')
    
    return render(request, 'finance/transactions/delete.html', {'transaction': transaction})


@login_required
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user).order_by('category')
    return render(request, 'finance/budgets/list.html', {'budgets': budgets})


@login_required
def budget_create(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Orçamento criado com sucesso!')
            return redirect('budget_list')
    else:
        form = BudgetForm(user=request.user)
    
    return render(request, 'finance/budgets/form.html', {'form': form, 'title': 'Novo Orçamento'})


@login_required
def budget_edit(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Orçamento atualizado com sucesso!')
            return redirect('budget_list')
    else:
        form = BudgetForm(instance=budget, user=request.user)
    
    return render(request, 'finance/budgets/form.html', {'form': form, 'title': 'Editar Orçamento'})


@login_required
def budget_delete(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Orçamento excluído com sucesso!')
        return redirect('budget_list')
    
    return render(request, 'finance/budgets/delete.html', {'budget': budget})


@login_required
def reports(request):
    # Dados para gráficos
    today = datetime.now().date()
    six_months_ago = today - relativedelta(months=6)
    
    # Gastos e receitas nos últimos 6 meses
    monthly_data = (
        Transaction.objects
        .filter(user=request.user, date__gte=six_months_ago)
        .extra({'month': "date_trunc('month', date)"})
        .values('month', 'transaction_type')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    
    # Preparar dados para o gráfico
    income_data = {}
    expense_data = {}
    
    for item in monthly_data:
        month = item['month'].strftime('%Y-%m')
        if item['transaction_type'] == 'IN':
            income_data[month] = float(item['total'])
        else:
            expense_data[month] = float(item['total'])
    
    # Gastos por categoria (últimos 3 meses)
    three_months_ago = today - relativedelta(months=3)
    category_data = (
        Transaction.objects
        .filter(user=request.user, transaction_type='OUT', date__gte=three_months_ago)
        .values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    
    context = {
        'income_data': json.dumps(income_data),
        'expense_data': json.dumps(expense_data),
        'category_data': category_data,
    }
    
    return render(request, 'finance/reports/index.html', context)


@login_required
def forecast(request):
    # Previsão para os próximos 3 meses
    today = datetime.now().date()
    three_months_later = today + relativedelta(months=3)
    
    # Saldo atual
    accounts = BankAccount.objects.filter(user=request.user, is_active=True)
    current_balance = sum(account.current_balance() for account in accounts)
    
    # Receitas recorrentes
    recurring_income = (
        Transaction.objects
        .filter(
            user=request.user,
            transaction_type='IN',
            is_recurrent=True,
            date__gte=today,
            date__lte=three_months_later
        )
        .order_by('date')
    )
    
    # Despesas recorrentes
    recurring_expenses = (
        Transaction.objects
        .filter(
            user=request.user,
            transaction_type='OUT',
            is_recurrent=True,
            date__gte=today,
            date__lte=three_months_later
        )
        .order_by('date')
    )
    
    # Previsão de saldo
    forecast_data = []
    balance = current_balance
    forecast_data.append({
        'date': today,
        'description': 'Saldo atual',
        'amount': balance,
        'balance': balance,
        'type': 'balance'
    })
    
    # Combinar e ordenar todas as transações recorrentes
    all_recurring = list(recurring_income) + list(recurring_expenses)
    all_recurring.sort(key=lambda x: x.date)
    
    for transaction in all_recurring:
        if transaction.transaction_type == 'IN':
            balance += transaction.amount
        else:
            balance -= transaction.amount
        
        forecast_data.append({
            'date': transaction.date,
            'description': transaction.description,
            'amount': transaction.amount,
            'balance': balance,
            'type': transaction.transaction_type.lower()
        })
    
    context = {
        'current_balance': current_balance,
        'forecast_data': forecast_data,
        'end_date': three_months_later,
    }
    
    return render(request, 'finance/reports/forecast.html', context)


@login_required
def get_account_balance(request, account_id):
    account = get_object_or_404(BankAccount, pk=account_id, user=request.user)
    return JsonResponse({'balance': account.current_balance()})


@login_required
def get_card_balance(request, card_id):
    card = get_object_or_404(CreditCard, pk=card_id, user=request.user)
    return JsonResponse({
        'balance': card.current_balance(),
        'available_limit': card.available_limit()
    })