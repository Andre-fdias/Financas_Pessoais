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
def conta_create(request):
    if request.method == 'POST':
        print("Dados POST recebidos:", request.POST)  # Debug
        form = ContaBancariaForm(request.POST, user=request.user)
        
        if form.is_valid():
            print("Formulário válido")  # Debug
            conta = form.save(commit=False)
            conta.proprietario = request.user
            conta.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Conta bancária adicionada com sucesso!'})
            else:
                messages.success(request, 'Conta bancária adicionada com sucesso!')
                return redirect('core:conta_list')
        else:
            print("Erros do formulário:", form.errors)  # Debug
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            else:
                return render(request, 'core/conta_form.html', {'form': form, 'action': 'Adicionar'})
    else:
        form = ContaBancariaForm(user=request.user)
        return render(request, 'core/conta_form.html', {'form': form, 'action': 'Adicionar'})

# Adicione BANCO_CHOICES ao contexto da view conta_list
@login_required
def conta_list(request):
    tipo_filtro = request.GET.get('tipo', None)
    status_filtro = request.GET.get('status', None)

    contas = ContaBancaria.objects.filter(proprietario=request.user)

    if tipo_filtro:
        contas = contas.filter(tipo=tipo_filtro)
    if status_filtro == 'ativa':
        contas = contas.filter(ativa=True)
    elif status_filtro == 'inativa':
        contas = contas.filter(ativa=False)

    contas_ativas = contas.filter(ativa=True).count()
    contas_inativas = contas.filter(ativa=False).count()
    total_contas = contas.count()

    percentual_ativas = (contas_ativas / total_contas * 100) if total_contas > 0 else 0
    percentual_inativas = (contas_inativas / total_contas * 100) if total_contas > 0 else 0
    
    # IMPORTANTE: Acessa as choices do campo 'tipo' do modelo ContaBancaria
    tipos_conta_choices = ContaBancaria._meta.get_field('tipo').choices

    # Passe BANCO_CHOICES e os tipos de conta para o contexto
    return render(request, 'core/conta_list.html', {
        'contas': contas,
        'contas_ativas': contas_ativas,
        'contas_inativas': contas_inativas,
        'percentual_ativas': round(percentual_ativas, 2),
        'percentual_inativas': round(percentual_inativas, 2),
        'tipo_filtro': tipo_filtro,
        'status_filtro': status_filtro,
        'tipos_conta': tipos_conta_choices, # AGORA ESTÁ CORRETO
        'banco_choices': BANCO_CHOICES # PASSA AS ESCOLHAS DO MODELO PARA O TEMPLATE
    })

# Nova view para o modal
@login_required
def conta_create_modal(request):
    if request.method == 'POST':
        form = ContaBancariaForm(request.POST, user=request.user)
        if form.is_valid():
            conta = form.save(commit=False)
            conta.proprietario = request.user
            conta.save()
            return JsonResponse({'success': True, 'message': 'Conta adicionada com sucesso!'})
        else:
            # Retorna os erros de validação
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [{'message': error} for error in error_list]
            return JsonResponse({'success': False, 'errors': errors}, status=400)
    else:
        form = ContaBancariaForm(user=request.user)
    return render(request, 'core/includes/conta_form_modal.html', {'form': form})


@login_required
def conta_update(request, pk):
    conta = get_object_or_404(ContaBancaria, pk=pk, proprietario=request.user)
    
    if request.method == 'POST':
        form = ContaBancariaForm(request.POST, instance=conta, user=request.user)
        
        if form.is_valid():
            form.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Conta bancária atualizada com sucesso!'})
            else:
                messages.success(request, 'Conta bancária atualizada com sucesso!')
                return redirect('core:conta_list')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            else:
                messages.error(request, 'Erro ao atualizar a conta bancária. Verifique os campos.')
                return render(request, 'core/conta_form.html', {'form': form, 'action': 'Atualizar'})
    
    # Para requisições GET, ainda redireciona para a página tradicional
    form = ContaBancariaForm(instance=conta, user=request.user)
    return render(request, 'core/conta_form.html', {'form': form, 'action': 'Atualizar'})


# Em views.py, modifique a view conta_delete:
@login_required
def conta_delete(request, pk):
    conta = get_object_or_404(ContaBancaria, pk=pk, proprietario=request.user)
    
    if request.method == 'POST':
        conta.delete()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Conta bancária excluída com sucesso!'})
        
        messages.success(request, 'Conta bancária excluída com sucesso!')
        return redirect('core:conta_list')
    
    # Se for GET, retorna o template tradicional (para navegadores sem JS)
    return render(request, 'core/conta_confirm_delete.html', {'conta': conta})




from django.contrib.auth.decorators import login_required


@login_required
def entrada_list(request):
    # Lista de meses para o filtro
    meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]
    
    # Obtém o ano e mês atual
    hoje = datetime.now()
    ano_atual = hoje.year
    mes_atual = hoje.month
    
    # Filtros - padrão para mês/ano atual
    ano_filtro = request.GET.get('ano', str(ano_atual))
    mes_filtro = request.GET.get('mes', str(mes_atual))
    forma_filtro = request.GET.get('forma')
    
    # Aplica os filtros
    entradas = Entrada.objects.filter(usuario=request.user)
    
    # Sempre filtra pelo ano selecionado (ou atual)
    entradas = entradas.filter(data__year=ano_filtro)
    
    # Se não tem filtro de mês ou é 'todos', usa o mês atual como padrão
    if not mes_filtro or mes_filtro == 'todos':
        mes_filtro = str(mes_atual)
        entradas = entradas.filter(data__month=mes_atual)
    else:
        entradas = entradas.filter(data__month=mes_filtro)
    
    if forma_filtro:
        entradas = entradas.filter(forma_recebimento=forma_filtro)
    
    # Cálculos para os cards (sempre baseado no filtro aplicado)
    total_filtrado = entradas.aggregate(total=Sum('valor'))['total'] or 0
    
    # Para cálculo da variação mensal, precisamos do mês anterior
    mes_para_calculo = int(mes_filtro) if mes_filtro and mes_filtro != 'todos' else mes_atual
    ano_para_calculo = int(ano_filtro)
    
    mes_anterior = mes_para_calculo - 1 if mes_para_calculo > 1 else 12
    ano_mes_anterior = ano_para_calculo if mes_para_calculo > 1 else ano_para_calculo - 1
    
    # Entradas do mês anterior para comparação
    entradas_mes_anterior = Entrada.objects.filter(
        usuario=request.user,
        data__month=mes_anterior,
        data__year=ano_mes_anterior
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    if entradas_mes_anterior > 0:
        variacao_mensal = round(((total_filtrado - entradas_mes_anterior) / entradas_mes_anterior * 100), 2)
    else:
        variacao_mensal = 0
    
    # Média mensal (considera todos os meses com registros)
    total_meses = Entrada.objects.filter(usuario=request.user).dates('data', 'month').count()
    total_geral = Entrada.objects.filter(usuario=request.user).aggregate(total=Sum('valor'))['total'] or 0
    media_mensal = round((total_geral / total_meses) if total_meses > 0 else 0, 2)
    
    # Nome do mês atual para o título
    mes_nome = dict(meses).get(int(mes_filtro) if mes_filtro and mes_filtro != 'todos' else mes_atual, '')
    
    return render(request, 'core/entrada_list.html', {
        'entradas': entradas.order_by('-data'),
        'meses': meses,
        'anos_disponiveis': list(range(ano_atual - 2, ano_atual + 1)),
        'ano_selecionado': int(ano_filtro),
        'mes_selecionado': str(mes_atual) if not mes_filtro or mes_filtro == 'todos' else mes_filtro,
        'forma_filtro': forma_filtro,
        'total_entradas': total_filtrado,
        'entradas_mes_atual': total_filtrado,  # Agora reflete o valor filtrado
        'media_mensal': media_mensal,
        'variacao_mensal': variacao_mensal,
        'mes_atual_nome': mes_nome,
        'ano_atual': ano_para_calculo,
    })

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




from django.contrib.auth.decorators import login_required
from django.views import View
from .models import CATEGORIA_CHOICES, SUBCATEGORIA_CHOICES

from datetime import datetime



@login_required
def saida_list(request):
    # Lista de meses para o filtro
    meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]
    
    # Obtém o ano e mês atual
    hoje = datetime.now()
    ano_atual = hoje.year
    mes_atual = hoje.month
    
    # Filtros - padrão para mês/ano atual
    ano_filtro = request.GET.get('ano', str(ano_atual))
    mes_filtro = request.GET.get('mes', str(mes_atual))
    status_filtro = request.GET.get('status')
    
    # Aplica os filtros
    saidas = Saida.objects.filter(usuario=request.user)
    
    # Sempre filtra pelo ano selecionado (ou atual)
    saidas = saidas.filter(data_vencimento__year=ano_filtro)
    
    # Se não tem filtro de mês ou é 'todos', usa o mês atual como padrão
    if not mes_filtro or mes_filtro == 'todos':
        mes_filtro = str(mes_atual)
        saidas = saidas.filter(data_vencimento__month=mes_atual)
    else:
        saidas = saidas.filter(data_vencimento__month=mes_filtro)
    
    if status_filtro:
        saidas = saidas.filter(situacao=status_filtro)
    
    # Cálculos para os cards (sempre baseado no filtro aplicado)
    total_filtrado = saidas.aggregate(total=Sum('valor'))['total'] or 0
    despesas_pagas = saidas.filter(situacao='pago').aggregate(total=Sum('valor'))['total'] or 0
    despesas_pendentes = saidas.filter(situacao='pendente').aggregate(total=Sum('valor'))['total'] or 0
    
    percentual_pago = round((despesas_pagas / total_filtrado * 100) if total_filtrado > 0 else 0, 2)
    percentual_pendente = round((despesas_pendentes / total_filtrado * 100) if total_filtrado > 0 else 0, 2)
    
    # Para cálculo da variação mensal, precisamos do mês anterior
    mes_para_calculo = int(mes_filtro) if mes_filtro and mes_filtro != 'todos' else mes_atual
    ano_para_calculo = int(ano_filtro)
    
    mes_anterior = mes_para_calculo - 1 if mes_para_calculo > 1 else 12
    ano_mes_anterior = ano_para_calculo if mes_para_calculo > 1 else ano_para_calculo - 1
    
    # Saídas do mês anterior para comparação
    saidas_mes_anterior = Saida.objects.filter(
        usuario=request.user,
        data_vencimento__month=mes_anterior,
        data_vencimento__year=ano_mes_anterior
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    if saidas_mes_anterior > 0:
        variacao_mensal = round(((total_filtrado - saidas_mes_anterior) / saidas_mes_anterior * 100), 2)
    else:
        variacao_mensal = 0
    
    # Nome do mês atual para o título
    mes_nome = dict(meses).get(int(mes_filtro) if mes_filtro and mes_filtro != 'todos' else mes_atual, '')
    
    return render(request, 'core/saida_list.html', {
        'saidas': saidas.order_by('-data_vencimento'),
        'meses': meses,
        'anos_disponiveis': list(range(ano_atual - 2, ano_atual + 1)),
        'ano_selecionado': int(ano_filtro),
        'mes_selecionado': str(mes_atual) if not mes_filtro or mes_filtro == 'todos' else mes_filtro,
        'status_filtro': status_filtro,
        'total_despesas': total_filtrado,
        'despesas_pagas': despesas_pagas,
        'despesas_pendentes': despesas_pendentes,
        'percentual_pago': percentual_pago,
        'percentual_pendente': percentual_pendente,
        'variacao_mensal': variacao_mensal,
        'mes_atual_nome': mes_nome,
        'ano_atual': ano_para_calculo,
    })


from django.contrib.auth.decorators import login_required


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
    # Lista de meses para o filtro
    meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]
    
    # Obtém o ano e mês atual
    hoje = datetime.now()
    ano_atual = hoje.year
    mes_atual = hoje.month
    
    # Filtros - padrão para mês/ano atual
    ano_filtro = request.GET.get('ano', str(ano_atual))
    mes_filtro = request.GET.get('mes', str(mes_atual))
    tipo_filtro = request.GET.get('tipo')
    
    # Obtém entradas e saídas
    entradas = Entrada.objects.filter(usuario=request.user)
    saidas = Saida.objects.filter(usuario=request.user)
    
    # Aplica filtros de data
    if mes_filtro and mes_filtro != 'todos':
        entradas = entradas.filter(data__month=mes_filtro)
        saidas = saidas.filter(data_vencimento__month=mes_filtro)
    
    entradas = entradas.filter(data__year=ano_filtro)
    saidas = saidas.filter(data_vencimento__year=ano_filtro)
    
    # Filtro por tipo (entrada/saída)
    if tipo_filtro == 'entrada':
        saidas = saidas.none()
    elif tipo_filtro == 'saida':
        entradas = entradas.none()
    
    # Combine e ordene por data
    transacoes = sorted(
        list(entradas) + list(saidas),
        key=lambda x: x.data if hasattr(x, 'data') else x.data_vencimento,
        reverse=True
    )
    
    # Cálculos para os cards
    total_entradas = entradas.aggregate(total=Sum('valor'))['total'] or 0
    total_saidas = saidas.aggregate(total=Sum('valor'))['total'] or 0
    saldo_mes = total_entradas - total_saidas
    
    # Variação mensal
    mes_para_calculo = int(mes_filtro) if mes_filtro and mes_filtro != 'todos' else mes_atual
    ano_para_calculo = int(ano_filtro)
    
    mes_anterior = mes_para_calculo - 1 if mes_para_calculo > 1 else 12
    ano_mes_anterior = ano_para_calculo if mes_para_calculo > 1 else ano_para_calculo - 1
    
    # Transações do mês anterior para comparação
    entradas_mes_anterior = Entrada.objects.filter(
        usuario=request.user,
        data__month=mes_anterior,
        data__year=ano_mes_anterior
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    saidas_mes_anterior = Saida.objects.filter(
        usuario=request.user,
        data_vencimento__month=mes_anterior,
        data_vencimento__year=ano_mes_anterior
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    saldo_mes_anterior = entradas_mes_anterior - saidas_mes_anterior
    
    if saldo_mes_anterior != 0:
        variacao_mensal = round(((saldo_mes - saldo_mes_anterior) / abs(saldo_mes_anterior) * 100, 2))
    else:
        variacao_mensal = 0
    
    # Nome do mês atual para o título
    mes_nome = dict(meses).get(int(mes_filtro) if mes_filtro and mes_filtro != 'todos' else mes_atual, '')
    
    return render(request, 'core/extrato_completo.html', {
        'transacoes': transacoes,
        'meses': meses,
        'anos_disponiveis': list(range(ano_atual - 2, ano_atual + 1)),
        'ano_selecionado': int(ano_filtro),
        'mes_selecionado': str(mes_atual) if not mes_filtro or mes_filtro == 'todos' else mes_filtro,
        'tipo_filtro': tipo_filtro,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo_mes': saldo_mes,
        'variacao_mensal': variacao_mensal,
        'mes_atual_nome': mes_nome,
        'ano_atual': ano_para_calculo,
    })


@login_required
def saldo_atual(request):
    # Filtra as contas bancárias pelo proprietário (usuário logado)
    contas = ContaBancaria.objects.filter(proprietario=request.user)
    
    saldo_por_conta = {}
    saldo_geral = 0
    
    for conta in contas:
        # Filtra Entradas e Saídas usando 'usuario' em vez de 'proprietario'
        entradas_conta = Entrada.objects.filter(usuario=request.user, conta_bancaria=conta).aggregate(Sum('valor'))['valor__sum'] or 0
        saidas_conta = Saida.objects.filter(usuario=request.user, conta_bancaria=conta).aggregate(Sum('valor'))['valor__sum'] or 0
        
        saldo = entradas_conta - saidas_conta
        saldo_por_conta[conta.get_nome_banco_display()] = saldo # Use get_nome_banco_display para o nome legível
        saldo_geral += saldo

    context = {
        'saldo_geral': saldo_geral,
        'saldo_por_conta': saldo_por_conta,
    }
    return render(request, 'core/saldo_atual.html', context)


 

######################
# Dashboard principal - VERSÃO COMPLETA
######################
from decimal import Decimal
import numpy as np
from sklearn.linear_model import LinearRegression
import json

# Funções auxiliares para padronização de dados
def get_sum(queryset):
    """Retorna a soma de 'valor' de um queryset como Decimal, ou 0 se vazio."""
    return queryset.aggregate(total=Sum('valor'))['total'] or Decimal('0')

@login_required
def dashboard(request):
    today = date.today()
    first_day_of_month = today.replace(day=1)

    # Período selecionado (padrão: 30 dias)
    periodo = request.GET.get('periodo', '30')
    if periodo == '30':
        data_inicio = today - timedelta(days=30)
    elif periodo == '90':
        data_inicio = today - timedelta(days=90)
    elif periodo == '365':
        data_inicio = today - timedelta(days=365)
    else:
        data_inicio = first_day_of_month  # padrão

    # Dados para os cards
    total_entradas = get_sum(Entrada.objects.filter(usuario=request.user, data__gte=data_inicio))
    total_saidas = get_sum(Saida.objects.filter(usuario=request.user, data_vencimento__gte=data_inicio))
    saldo_geral = total_entradas - total_saidas

    # Entradas e Saídas do mês atual
    entradas_mes = get_sum(Entrada.objects.filter(usuario=request.user, data__year=today.year, data__month=today.month))
    saidas_mes = get_sum(Saida.objects.filter(usuario=request.user, data_vencimento__year=today.year, data_vencimento__month=today.month))

    # Variação mensal
    mes_anterior = today.month - 1 if today.month > 1 else 12
    ano_mes_anterior = today.year if today.month > 1 else today.year - 1

    entradas_mes_anterior = get_sum(Entrada.objects.filter(usuario=request.user, data__month=mes_anterior, data__year=ano_mes_anterior))
    saidas_mes_anterior = get_sum(Saida.objects.filter(usuario=request.user, data_vencimento__month=mes_anterior, data_vencimento__year=ano_mes_anterior))

    variacao_receitas = Decimal('0.00')
    if entradas_mes_anterior > 0:
        variacao_receitas = ((entradas_mes - entradas_mes_anterior) / entradas_mes_anterior * 100).quantize(Decimal('0.01'))

    variacao_despesas = Decimal('0.00')
    if saidas_mes_anterior > 0:
        variacao_despesas = ((saidas_mes - saidas_mes_anterior) / saidas_mes_anterior * 100).quantize(Decimal('0.01'))

    # Dados para gráficos mensais (últimos 7 meses)
    meses_labels = []
    receitas_mensais_data = []
    despesas_mensais_data = []
    saldo_mensal_data = []

    for i in range(6, -1, -1):
        mes = today.month - i
        ano = today.year
        if mes < 1:
            mes += 12
            ano -= 1
        meses_labels.append(f"{mes}/{ano}")

        entradas = get_sum(Entrada.objects.filter(usuario=request.user, data__month=mes, data__year=ano))
        saidas = get_sum(Saida.objects.filter(usuario=request.user, data_vencimento__month=mes, data_vencimento__year=ano))

        receitas_mensais_data.append(float(entradas))
        despesas_mensais_data.append(float(saidas))
        saldo_mensal_data.append(float(entradas - saidas))

    # Saldo acumulado mensal
    saldo_acumulado_data = []
    saldo = Decimal('0.00')
    for rec, desp in zip(receitas_mensais_data, despesas_mensais_data):
        saldo += Decimal(str(rec)) - Decimal(str(desp))
        saldo_acumulado_data.append(float(saldo))

    # Gráfico de categorias
    categorias = Saida.objects.filter(usuario=request.user).values('categoria').annotate(total=Sum('valor'))
    categorias_labels = [dict(CATEGORIA_CHOICES).get(c['categoria'], c['categoria']) for c in categorias]
    categorias_data = [float(c['total']) for c in categorias]

    # Gráfico de forma de pagamento
    FORMA_PAGAMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('pix', 'PIX'),
        ('boleto', 'Boleto'),
        ('cheque', 'Cheque'),
        ('outros', 'Outros'),
    ]
    formas_pagamento = Saida.objects.filter(usuario=request.user).values('forma_pagamento').annotate(total=Sum('valor'))
    formas_pagamento_labels = [dict(FORMA_PAGAMENTO_CHOICES).get(f['forma_pagamento'], f['forma_pagamento']) for f in formas_pagamento]
    formas_pagamento_data = [float(f['total']) for f in formas_pagamento]

    # Despesas fixas vs variáveis
    despesas_fixas = get_sum(Saida.objects.filter(usuario=request.user, recorrente__in=['mensal', 'anual']))
    despesas_variaveis = get_sum(Saida.objects.filter(usuario=request.user, recorrente='unica'))
    total_despesas = despesas_fixas + despesas_variaveis
    percentual_fixas = (despesas_fixas / total_despesas * 100).quantize(Decimal('0')) if total_despesas > 0 else Decimal('0')
    percentual_variaveis = (despesas_variaveis / total_despesas * 100).quantize(Decimal('0')) if total_despesas > 0 else Decimal('0')

    # Status de pagamentos
    pagos_total = get_sum(Saida.objects.filter(usuario=request.user, situacao='pago'))
    pendentes_total = get_sum(Saida.objects.filter(usuario=request.user, situacao='pendente'))
    total_status = pagos_total + pendentes_total
    percentual_pagos = (pagos_total / total_status * 100).quantize(Decimal('0')) if total_status > 0 else Decimal('0')
    percentual_pendentes = (pendentes_total / total_status * 100).quantize(Decimal('0')) if total_status > 0 else Decimal('0')

    # Últimas transações
    ultimas_entradas = Entrada.objects.filter(usuario=request.user).order_by('-data')[:5]
    ultimas_saidas = Saida.objects.filter(usuario=request.user).order_by('-data_vencimento')[:5]

    def get_transaction_date(obj):
        return getattr(obj, 'data', getattr(obj, 'data_vencimento', None))

    ultimas_transacoes = sorted(list(ultimas_entradas) + list(ultimas_saidas), key=get_transaction_date, reverse=True)[:10]

    # ===== NOVAS ANÁLISES =====
    sazonalidade_data = calcular_sazonalidade(request.user)
    projecao_receitas, projecao_despesas, projecao_saldo = calcular_projecao_futura(request.user, meses=6)
    indicadores = calcular_indicadores_saude_financeira(request.user)
    analise_comportamental = calcular_analise_comportamental(request.user)
    simulacoes = calcular_simulacoes_cenarios(request.user)
    analise_riscos = calcular_analise_riscos(request.user)
    otimizacao_investimentos = calcular_otimizacao_investimentos(request.user)

    context = {
        'saldo_geral': saldo_geral,
        'entradas_mes': entradas_mes,
        'saidas_mes': saidas_mes,
        'variacao_receitas': variacao_receitas,
        'variacao_despesas': variacao_despesas,
        'ultimas_transacoes': ultimas_transacoes,
        'meses_labels': json.dumps(meses_labels),
        'saldo_acumulado_data': json.dumps(saldo_acumulado_data),
        'saldo_mensal_data': json.dumps(saldo_mensal_data),
        'meses_comparativo_labels': json.dumps(meses_labels),
        'receitas_mensais_data': json.dumps(receitas_mensais_data),
        'despesas_mensais_data': json.dumps(despesas_mensais_data),
        'categorias_labels': json.dumps(categorias_labels),
        'categorias_data': json.dumps(categorias_data),
        'formas_pagamento_labels': json.dumps(formas_pagamento_labels),
        'formas_pagamento_data': json.dumps(formas_pagamento_data),
        'despesas_fixas': despesas_fixas,
        'despesas_variaveis': despesas_variaveis,
        'percentual_fixas': percentual_fixas,
        'percentual_variaveis': percentual_variaveis,
        'pagos_total': pagos_total,
        'pendentes_total': pendentes_total,
        'percentual_pagos': percentual_pagos,
        'percentual_pendentes': percentual_pendentes,
        'sazonalidade_labels': json.dumps(list(sazonalidade_data.keys())),
        'sazonalidade_values': json.dumps([float(v) for v in sazonalidade_data.values()]),
        'projecao_labels': json.dumps([f"Mês {i+1}" for i in range(len(projecao_receitas))]),
        'projecao_receitas': json.dumps([float(v) for v in projecao_receitas]),
        'projecao_despesas': json.dumps([float(v) for v in projecao_despesas]),
        'projecao_saldo': json.dumps([float(v) for v in projecao_saldo]),
        'indicadores': indicadores,
        'analise_comportamental': analise_comportamental,
        'simulacoes': simulacoes,
        'analise_riscos': analise_riscos,
               'otimizacao_investimentos': {
            'sugestao': otimizacao_investimentos['sugestao'],
            'alocacao': otimizacao_investimentos['alocacao'], # Mantém o dicionário para os filtros do template
            'alocacao_labels': json.dumps(list(otimizacao_investimentos['alocacao'].keys())),
            'alocacao_values': json.dumps(list(otimizacao_investimentos['alocacao'].values()))
        }
    }

    return render(request, 'core/dashboard.html', context)


# ===== FUNÇÕES DE ANÁLISE =====


# ===== FUNÇÕES DE ANÁLISE REVISADAS =====

def calcular_sazonalidade(usuario):
    """Calcula padrões sazonais nos gastos e receitas"""
    sazonalidade = {}
    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dec']
    for mes in range(1, 13):
        entradas_mes = get_sum(Entrada.objects.filter(usuario=usuario, data__month=mes))
        saidas_mes = get_sum(Saida.objects.filter(usuario=usuario, data_vencimento__month=mes))
        sazonalidade[meses[mes-1]] = entradas_mes - saidas_mes
    return sazonalidade

def calcular_projecao_futura(usuario, meses=6):
    """Calcula projeções futuras baseadas em tendências históricas"""
    historico_receitas = []
    historico_despesas = []
    today = date.today()
    for i in range(12, 0, -1):
        mes = today.month - i
        ano = today.year
        if mes < 1:
            mes += 12
            ano -= 1
        entradas = get_sum(Entrada.objects.filter(usuario=usuario, data__month=mes, data__year=ano))
        saidas = get_sum(Saida.objects.filter(usuario=usuario, data_vencimento__month=mes, data_vencimento__year=ano))
        historico_receitas.append(float(entradas))
        historico_despesas.append(float(saidas))
    X = np.array(range(len(historico_receitas))).reshape(-1, 1)
    modelo_receitas = LinearRegression().fit(X, historico_receitas)
    modelo_despesas = LinearRegression().fit(X, historico_despesas)
    futuro_X = np.array(range(len(historico_receitas), len(historico_receitas) + meses)).reshape(-1, 1)
    projecao_receitas = [Decimal(str(x)).quantize(Decimal('0.01')) for x in modelo_receitas.predict(futuro_X).tolist()]
    projecao_despesas = [Decimal(str(x)).quantize(Decimal('0.01')) for x in modelo_despesas.predict(futuro_X).tolist()]
    projecao_saldo = [r - d for r, d in zip(projecao_receitas, projecao_despesas)]
    projecao_receitas = [max(Decimal('0'), x) for x in projecao_receitas]
    projecao_despesas = [max(Decimal('0'), x) for x in projecao_despesas]
    return projecao_receitas, projecao_despesas, projecao_saldo


def calcular_indicadores_saude_financeira(usuario):
    """Calcula indicadores de saúde financeira"""
    total_entradas = get_sum(Entrada.objects.filter(usuario=usuario))
    total_saidas = get_sum(Saida.objects.filter(usuario=usuario))
    saldo = total_entradas - total_saidas
    despesas_fixas_mensais = get_sum(Saida.objects.filter(usuario=usuario, recorrente='mensal'))
    indicadores = {
        'liquidez_corrente': (total_entradas / total_saidas * 100).quantize(Decimal('0.01')) if total_saidas > 0 else Decimal('0'),
        'margem_seguranca': ((total_entradas - total_saidas) / total_entradas * 100).quantize(Decimal('0.01')) if total_entradas > 0 else Decimal('0'),
        'endividamento': (total_saidas / total_entradas * 100).quantize(Decimal('0.01')) if total_entradas > 0 else Decimal('0'),
        'poupanca_mensal': (saldo / 12).quantize(Decimal('0.01')) if saldo > 0 else Decimal('0'),
        'reserva_emergencia': (despesas_fixas_mensais * 3).quantize(Decimal('0.01')),
    }
    return indicadores


def calcular_indicadores_saude_financeira(usuario):
    """Calcula indicadores de saúde financeira"""
    # Dados básicos
    total_entradas = Entrada.objects.filter(usuario=usuario).aggregate(total=Sum('valor'))['total'] or 0
    total_saidas = Saida.objects.filter(usuario=usuario).aggregate(total=Sum('valor'))['total'] or 0
    saldo = total_entradas - total_saidas
    
    # Despesas fixas mensais
    despesas_fixas_mensais = Saida.objects.filter(
        usuario=usuario,
        recorrente='mensal'
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    # Indicadores
    indicadores = {
        'liquidez_corrente': round(float(saldo) / float(total_saidas) * 100, 2) if total_saidas > 0 else 0,
        'margem_seguranca': round((float(total_entradas) - float(total_saidas)) / float(total_entradas) * 100, 2) if total_entradas > 0 else 0,
        'endividamento': round(float(total_saidas) / float(total_entradas) * 100, 2) if total_entradas > 0 else 0,
        'poupanca_mensal': round(float(saldo) / 12, 2) if saldo > 0 else 0,
        'reserva_emergencia': round(float(despesas_fixas_mensais) * 6, 2),  # 6 meses de despesas
    }
    
    return indicadores

def calcular_analise_comportamental(usuario):
    """Analisa padrões comportamentais nos gastos"""
    gastos_por_dia = {}
    dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    for saida in Saida.objects.filter(usuario=usuario):
        dia_semana = saida.data_vencimento.weekday()
        valor = saida.valor or Decimal('0')
        gastos_por_dia[dias_semana[dia_semana]] = gastos_por_dia.get(dias_semana[dia_semana], Decimal('0')) + valor
    categorias_comportamento = {'essenciais': Decimal('0'), 'supérfluos': Decimal('0'), 'investimentos': Decimal('0')}
    categorias_essenciais = ['moradia', 'alimentacao', 'transporte', 'saude', 'educacao']
    categorias_superfluos = ['lazer', 'pessoais', 'familia']
    categorias_investimentos = ['investimentos']
    for saida in Saida.objects.filter(usuario=usuario):
        valor = saida.valor or Decimal('0')
        if saida.categoria in categorias_essenciais:
            categorias_comportamento['essenciais'] += valor
        elif saida.categoria in categorias_superfluos:
            categorias_comportamento['supérfluos'] += valor
        elif saida.categoria in categorias_investimentos:
            categorias_comportamento['investimentos'] += valor
    return {
        'gastos_por_dia': {k: float(v) for k, v in gastos_por_dia.items()},
        'categorias_comportamento': {k: float(v) for k, v in categorias_comportamento.items()}
    }

def calcular_simulacoes_cenarios(usuario):
    """Simula diferentes cenários financeiros"""
    total_entradas = get_sum(Entrada.objects.filter(usuario=usuario))
    total_saidas = get_sum(Saida.objects.filter(usuario=usuario))
    cenarios = {
        'aumento_10_despesas': (total_saidas * Decimal('1.1')).quantize(Decimal('0.01')),
        'reducao_10_despesas': (total_saidas * Decimal('0.9')).quantize(Decimal('0.01')),
        'aumento_10_receitas': (total_entradas * Decimal('1.1')).quantize(Decimal('0.01')),
        'reducao_10_receitas': (total_entradas * Decimal('0.9')).quantize(Decimal('0.01')),
        'impacto_inflacao_5': (total_saidas * Decimal('1.05')).quantize(Decimal('0.01')),
    }
    return cenarios

def calcular_analise_riscos(usuario):
    """Analisa riscos financeiros"""
    fontes_renda = Entrada.objects.filter(usuario=usuario).values('local').annotate(total=Sum('valor'))
    total_entradas = get_sum(Entrada.objects.filter(usuario=usuario))
    concentracao_risco = Decimal('0.00')
    if fontes_renda and total_entradas > 0:
        maior_fonte = max(fontes_renda, key=lambda x: x['total'])
        concentracao_risco = (maior_fonte['total'] / total_entradas * 100).quantize(Decimal('0.01'))
    despesas_mensais = get_sum(Saida.objects.filter(usuario=usuario)) / 12 if Saida.objects.filter(usuario=usuario).exists() else Decimal('0')
    reserva_ideal = (despesas_mensais * 6).quantize(Decimal('0.01'))
    return {
        'concentracao_risco': float(concentracao_risco),
        'reserva_ideal': float(reserva_ideal),
        'nivel_risco': 'Alto' if concentracao_risco > 50 else 'Moderado' if concentracao_risco > 30 else 'Baixo'
    }


def calcular_otimizacao_investimentos(usuario):
    """Sugere otimizações de investimentos"""
    saldo_atual = get_sum(Entrada.objects.filter(usuario=usuario)) - get_sum(Saida.objects.filter(usuario=usuario))
    if saldo_atual < Decimal('1000'):
        return {'sugestao': 'Foque em construir reserva de emergência primeiro', 'alocacao': {'Reserva Emergencial': 100, 'Investimentos': 0}}
    elif saldo_atual < Decimal('5000'):
        return {'sugestao': 'Diversifique entre reserva e investimentos conservadores', 'alocacao': {'Reserva Emergencial': 70, 'Renda Fixa': 30}}
    else:
        return {'sugestao': 'Considere diversificar com investimentos de maior risco e retorno', 'alocacao': {'Reserva Emergencial': 30, 'Renda Fixa': 40, 'Renda Variável': 30}}

# Demais views (home, register, etc.) não foram alteradas pois não apresentavam o erro de tipo.

    # Adicione estas funções em views.py:

def get_contas_bancarias_data(usuario):
    contas = ContaBancaria.objects.filter(proprietario=usuario, ativa=True)
    labels = [str(conta) for conta in contas]
    data = []
    for conta in contas:
        total_despesas = Saida.objects.filter(
            usuario=usuario, 
            conta_bancaria=conta
        ).aggregate(total=Sum('valor'))['total'] or 0
        data.append(float(total_despesas))
    return labels, data

def get_entradas_tipo_data(usuario):
    # Implementar lógica para agrupar entradas por tipo
    return ['Única', 'Mensal', 'Anual'], [100, 200, 50]  # Exemplo
