from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from .models import Transaction

def calculate_monthly_summary(user, months=6):
    """Calcula um resumo mensal de entradas e saídas"""
    end_date = datetime.now().date()
    start_date = end_date - relativedelta(months=months)
    
    monthly_data = (
        Transaction.objects
        .filter(user=user, date__gte=start_date, date__lte=end_date)
        .extra({'month': "date_trunc('month', date)"})
        .values('month', 'transaction_type')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    
    summary = {}
    for item in monthly_data:
        month = item['month'].strftime('%Y-%m')
        if month not in summary:
            summary[month] = {'income': 0, 'expense': 0}
        
        if item['transaction_type'] == 'IN':
            summary[month]['income'] = float(item['total'])
        else:
            summary[month]['expense'] = float(item['total'])
    
    return summary

def get_financial_forecast(user, months=3):
    """Gera uma previsão financeira para os próximos meses"""
    today = datetime.now().date()
    end_date = today + relativedelta(months=months)
    
    # Saldo atual
    accounts = BankAccount.objects.filter(user=user, is_active=True)
    current_balance = sum(account.current_balance() for account in accounts)
    
    # Transações recorrentes futuras
    recurring_transactions = (
        Transaction.objects
        .filter(
            user=user,
            is_recurrent=True,
            date__gte=today,
            date__lte=end_date
        )
        .order_by('date')
    )
    
    # Criar linha do tempo
    timeline = []
    balance = current_balance
    timeline.append({
        'date': today,
        'description': 'Saldo Atual',
        'amount': balance,
        'balance': balance,
        'type': 'balance'
    })
    
    for transaction in recurring_transactions:
        if transaction.transaction_type == 'IN':
            balance += transaction.amount
        else:
            balance -= transaction.amount
        
        timeline.append({
            'date': transaction.date,
            'description': transaction.description,
            'amount': transaction.amount,
            'balance': balance,
            'type': transaction.transaction_type.lower()
        })
    
    return timeline

def check_budget_alerts(user):
    """Verifica orçamentos e retorna alertas para gastos excessivos"""
    alerts = []
    budgets = Budget.objects.filter(user=user)
    
    for budget in budgets:
        percentage = budget.percentage_spent()
        if percentage > 100:
            alerts.append({
                'type': 'danger',
                'message': f'Orçamento de {budget.get_category_display()} excedido em {percentage - 100:.0f}%'
            })
        elif percentage > 80:
            alerts.append({
                'type': 'warning',
                'message': f'Orçamento de {budget.get_category_display()} está em {percentage:.0f}%'
            })
    
    return alerts