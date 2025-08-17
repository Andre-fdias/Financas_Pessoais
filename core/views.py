from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomUserCreationForm

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ContaBancaria, Entrada, Saida, BANCO_CHOICES
from .forms import ContaBancariaForm, EntradaForm, SaidaForm
from django.db.models import Sum
from datetime import date, timedelta
from django.http import JsonResponse

@login_required
def home(request):
    return render(request, 'core/home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Conta criada para {username}! Faça login para continuar.')
            return redirect('core:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})


from django.http import HttpResponse
from django.views.decorators.http import require_GET

@require_GET
def get_banco_code(request):
    nome_banco = request.GET.get('nome_banco')
    # Encontra o código correspondente ao nome do banco
    for bank_code, bank_name in BANCO_CHOICES:
        if bank_code == nome_banco:
            return HttpResponse(bank_code)
    return HttpResponse('')


@login_required
def conta_list(request):
    contas = ContaBancaria.objects.filter(proprietario=request.user)
    return render(request, 'core/conta_list.html', {'contas': contas})


@login_required
def conta_create(request):
    if request.method == 'POST':
        form = ContaBancariaForm(request.POST, user=request.user)
        if form.is_valid():
            conta = form.save(commit=False)
            conta.save()
            messages.success(request, 'Conta bancária criada com sucesso!')
            return redirect('core:conta_list')
    else:
        form = ContaBancariaForm(user=request.user)
    return render(request, 'core/conta_form.html', {'form': form, 'action': 'Criar'})

@login_required
def conta_update(request, pk):
    conta = get_object_or_404(ContaBancaria, pk=pk, proprietario=request.user)
    if request.method == 'POST':
        form = ContaBancariaForm(request.POST, instance=conta, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conta bancária atualizada com sucesso!')
            return redirect('core:conta_list')
    else:
        form = ContaBancariaForm(instance=conta, user=request.user)
    return render(request, 'core/conta_form.html', {'form': form, 'action': 'Atualizar'})


@login_required
def conta_delete(request, pk):
    conta = get_object_or_404(ContaBancaria, pk=pk, proprietario=request.user)
    if request.method == 'POST':
        conta.delete()
        messages.success(request, 'Conta bancária excluída com sucesso!')
        return redirect('core:conta_list')
    return render(request, 'core/conta_confirm_delete.html', {'conta': conta})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Entrada
from .forms import EntradaForm

@login_required
def entrada_list(request):
    entradas = Entrada.objects.filter(usuario=request.user).order_by('-data')
    return render(request, 'core/entrada_list.html', {'entradas': entradas})

@login_required
def entrada_create(request):
    if request.method == 'POST':
        form = EntradaForm(request.POST, user=request.user)
        if form.is_valid():
            entrada = form.save(commit=False)
            entrada.usuario = request.user
            entrada.save()
            messages.success(request, 'Entrada criada com sucesso!')
            return redirect('core:entrada_list')
    else:
        form = EntradaForm(user=request.user)
    return render(request, 'core/entrada_form.html', {'form': form, 'action': 'Criar'})

@login_required
def entrada_update(request, pk):
    entrada = get_object_or_404(Entrada, pk=pk, usuario=request.user)
    if request.method == 'POST':
        form = EntradaForm(request.POST, instance=entrada, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entrada atualizada com sucesso!')
            return redirect('core:entrada_list')
    else:
        form = EntradaForm(instance=entrada, user=request.user)
    return render(request, 'core/entrada_form.html', {'form': form, 'action': 'Atualizar'})

@login_required
def entrada_delete(request, pk):
    entrada = get_object_or_404(Entrada, pk=pk, usuario=request.user)
    if request.method == 'POST':
        entrada.delete()
        messages.success(request, 'Entrada excluída com sucesso!')
        return redirect('core:entrada_list')
    return render(request, 'core/entrada_confirm_delete.html', {'entrada': entrada})




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views import View
from .models import Saida, CATEGORIA_CHOICES, SUBCATEGORIA_CHOICES
from .forms import SaidaForm

from datetime import datetime



@login_required
def saida_list(request):
    # Lista de meses para o filtro
    meses = [
        (1, 'Jan'), (2, 'Fev'), (3, 'Mar'), (4, 'Abr'),
        (5, 'Mai'), (6, 'Jun'), (7, 'Jul'), (8, 'Ago'),
        (9, 'Set'), (10, 'Out'), (11, 'Nov'), (12, 'Dez')
    ]
    
    # Obtém o ano atual como padrão
    ano_atual = datetime.now().year
    anos_disponiveis = list(range(ano_atual - 2, ano_atual + 1))  # Últimos 2 anos e atual
    
    # Filtros
    ano_filtro = request.GET.get('ano', str(ano_atual))
    mes_filtro = request.GET.get('mes')
    status_filtro = request.GET.get('status')
    
    # Aplica os filtros
    saidas = Saida.objects.filter(usuario=request.user)
    saidas = saidas.filter(data_vencimento__year=ano_filtro)
    
    if mes_filtro and mes_filtro != 'todos':
        saidas = saidas.filter(data_vencimento__month=mes_filtro)
    
    if status_filtro:
        saidas = saidas.filter(situacao=status_filtro)
    
    # Cálculos para os cards
    total_despesas = saidas.aggregate(total=Sum('valor'))['total'] or 0
    despesas_pagas = saidas.filter(situacao='pago').aggregate(total=Sum('valor'))['total'] or 0
    despesas_pendentes = saidas.filter(situacao='pendente').aggregate(total=Sum('valor'))['total'] or 0
    
    percentual_pago = round((despesas_pagas / total_despesas * 100) if total_despesas > 0 else 0, 2)
    percentual_pendente = round((despesas_pendentes / total_despesas * 100) if total_despesas > 0 else 0, 2)
    
    # Cálculo da variação mensal (simplificado)
    mes_atual = datetime.now().month
    despesas_mes_atual = saidas.filter(data_vencimento__month=mes_atual).aggregate(total=Sum('valor'))['total'] or 0
    despesas_mes_anterior = saidas.filter(data_vencimento__month=mes_atual-1).aggregate(total=Sum('valor'))['total'] or 0
    
    if despesas_mes_anterior > 0:
        variacao_mensal = round(((despesas_mes_atual - despesas_mes_anterior) / despesas_mes_anterior * 100), 2)
    else:
        variacao_mensal = 0
    
    return render(request, 'core/saida_list.html', {
        'saidas': saidas.order_by('-data_vencimento'),
        'meses': meses,
        'anos_disponiveis': anos_disponiveis,
        'ano_selecionado': int(ano_filtro),
        'mes_selecionado': mes_filtro,
        'status_filtro': status_filtro,
        'total_despesas': total_despesas,
        'despesas_pagas': despesas_pagas,
        'despesas_pendentes': despesas_pendentes,
        'percentual_pago': percentual_pago,
        'percentual_pendente': percentual_pendente,
        'variacao_mensal': variacao_mensal,
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ContaBancaria, Entrada, Saida, BANCO_CHOICES
from .forms import ContaBancariaForm, EntradaForm, SaidaForm
from django.db.models import Sum
from datetime import date
from django.http import JsonResponse


from django.utils import timezone
from dateutil.relativedelta import relativedelta  # Adicione esta dependência

@login_required
def saida_create(request):
    parcelas_choices = list(range(1, 101))
    if request.method == 'POST':
        form = SaidaForm(request.POST, user=request.user)
        if form.is_valid():
            saida = form.save(commit=False)
            saida.usuario = request.user
            if saida.tipo_pagamento_detalhe == 'parcelado' and saida.quantidade_parcelas > 1:
                vencimento_base = saida.data_vencimento
                for parcela in range(saida.quantidade_parcelas):
                    # Calcula data do vencimento da parcela
                    vencimento = vencimento_base + relativedelta(months=parcela)
                    Saida.objects.create(
                        usuario=saida.usuario,
                        conta_bancaria=saida.conta_bancaria,
                        nome=f"{saida.nome} (Parcela {parcela+1}/{saida.quantidade_parcelas})",
                        valor=saida.valor_parcela,
                        valor_parcela=saida.valor_parcela,
                        data_lancamento=saida.data_lancamento,
                        data_vencimento=vencimento,
                        local=saida.local,
                        categoria=saida.categoria,
                        subcategoria=saida.subcategoria,
                        forma_pagamento=saida.forma_pagamento,
                        tipo_pagamento_detalhe=saida.tipo_pagamento_detalhe,
                        situacao=saida.situacao,
                        quantidade_parcelas=1,  # Cada cadastro é de uma parcela só!
                        recorrente='unica',
                        observacao=saida.observacao,
                    )
                messages.success(request, f'{saida.quantidade_parcelas} parcelas cadastradas com sucesso!')
            else:
                saida.save()
                messages.success(request, 'Saída cadastrada com sucesso!')
            return redirect('core:saida_list')
    else:
        form = SaidaForm(user=request.user)
    return render(
        request,
        'core/saida_form.html',
        {
            'form': form,
            'action': 'Criar',
            'parcelas_choices': parcelas_choices
        }
    )


@login_required
def saida_update(request, pk):
    saida = get_object_or_404(Saida, pk=pk, usuario=request.user)
    if request.method == 'POST':
        form = SaidaForm(request.POST, instance=saida, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Saída atualizada com sucesso!')
            return redirect('core:saida_list')
    else:
        form = SaidaForm(instance=saida, user=request.user)
    return render(request, 'core/saida_form.html', {
        'form': form,
        'action': 'Atualizar'
    })



@login_required
def saida_delete(request, pk):
    saida = get_object_or_404(Saida, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        saida.delete()
        messages.success(request, 'Saída excluída com sucesso!')
        return redirect('core:saida_list')
    
    return render(request, 'core/saida_confirm_delete.html', {
        'saida': saida
    })

class GetSubcategoriasView(View):
    def get(self, request, *args, **kwargs):
        categoria = request.GET.get('categoria')
        subcategorias = [
            {'id': sc[0], 'nome': sc[1]} 
            for sc in SUBCATEGORIA_CHOICES 
            if sc[2] == categoria
        ]
        return JsonResponse(subcategorias, safe=False)
    
    

@login_required
def extrato_completo(request):
    entradas = Entrada.objects.filter(usuario=request.user).order_by('-data')
    saidas = Saida.objects.filter(usuario=request.user).order_by('-data')

    # Combine e ordene por data
    transacoes = sorted(list(entradas) + list(saidas), key=lambda x: x.data, reverse=True)

    return render(request, 'core/extrato_completo.html', {'transacoes': transacoes})


@login_required
def saldo_atual(request):
    total_entradas = Entrada.objects.filter(usuario=request.user).aggregate(Sum('valor'))['valor__sum'] or 0
    total_saidas = Saida.objects.filter(usuario=request.user).aggregate(Sum('valor'))['valor__sum'] or 0
    saldo_geral = total_entradas - total_saidas

    contas = ContaBancaria.objects.filter(usuario=request.user)
    saldo_por_conta = {}
    for conta in contas:
        entradas_conta = Entrada.objects.filter(usuario=request.user, conta_bancaria=conta).aggregate(Sum('valor'))['valor__sum'] or 0
        saidas_conta = Saida.objects.filter(usuario=request.user, conta_bancaria=conta).aggregate(Sum('valor'))['valor__sum'] or 0
        saldo_por_conta[conta.nome_banco] = entradas_conta - saidas_conta

    return render(request, 'core/saldo_atual.html', {
        'saldo_geral': saldo_geral,
        'saldo_por_conta': saldo_por_conta,
    })


 

######################
# Dashboard principal
######################
@login_required
def dashboard(request):
    today = date.today()
    first_day_of_month = today.replace(day=1)

    # Saldo geral
    total_entradas = Entrada.objects.filter(usuario=request.user).aggregate(Sum('valor'))['valor__sum'] or 0
    total_saidas = Saida.objects.filter(usuario=request.user).aggregate(Sum('valor'))['valor__sum'] or 0
    saldo_geral = total_entradas - total_saidas

    # Entradas do mês
    entradas_mes = Entrada.objects.filter(
        usuario=request.user,
        data__gte=first_day_of_month,
        data__lte=today
    ).aggregate(Sum('valor'))['valor__sum'] or 0

    # Saídas do mês (considerando lógica de parcelamento)
    saidas_mes = 0
    for saida in Saida.objects.filter(usuario=request.user):
        if saida.situacao == 'pago' and saida.data_lancamento.month == today.month:
            if saida.tipo_pagamento_detalhe == 'avista':
                saidas_mes += float(saida.valor)
            else:  # parcelado
                saidas_mes += float(saida.valor_parcela)

    # Últimas Transações
    ultimas_entradas = Entrada.objects.filter(usuario=request.user).order_by('-data')[:5]
    ultimas_saidas = Saida.objects.filter(usuario=request.user).order_by('-data_lancamento')[:5]
    
    def get_transaction_date(obj):
        return getattr(obj, 'data', getattr(obj, 'data_lancamento', None))
    
    ultimas_transacoes = sorted(
        list(ultimas_entradas) + list(ultimas_saidas),
        key=get_transaction_date,
        reverse=True
    )[:5]

    context = {
        'saldo_geral': saldo_geral,
        'entradas_mes': entradas_mes,
        'saidas_mes': saidas_mes,
        'ultimas_transacoes': ultimas_transacoes,
    }
    return render(request, 'core/dashboard.html', context)