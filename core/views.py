from django.shortcuts import render, redirect, get_object_or_404

from .forms import CustomUserCreationForm, ProfileUpdateForm

from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ContaBancaria, Entrada, Saida, BANCO_CHOICES, FORMA_PAGAMENTO_CHOICES, FORMA_RECEBIMENTO_CHOICES, TIPO_PAGAMENTO_DETALHE_CHOICES, SITUACAO_CHOICES
from .forms import ContaBancariaForm, EntradaForm, SaidaForm, TransferenciaForm
from django.db.models import Sum
from datetime import date, timedelta, datetime,timezone # Mantém datetime para outras partes do código
from django.utils import timezone as dj_timezone # Alias para evitar conflito com datetime.timezone
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db import transaction
from decimal import Decimal
import json # Já estava importado, mas é bom garantir
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Q # Importante para combinar querysets
from dateutil.relativedelta import relativedelta
import numpy as np
from sklearn.linear_model import LinearRegression

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from datetime import datetime
from .models import Entrada, ContaBancaria
from .models import FORMA_RECEBIMENTO_CHOICES
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from decimal import Decimal
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .models import Entrada, Saida, ContaBancaria
from decimal import Decimal
import numpy as np
from sklearn.linear_model import LinearRegression
import json


# Funções auxiliares (se já existirem, apenas mantenha)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ContaBancaria, Entrada, Saida, BANCO_CHOICES, ContaBancaria # Importe ContaBancaria novamente para acessar choices de tipo
from django.db.models import Sum
from datetime import date, timedelta
from django.http import JsonResponse
import json # Importe para serializar dados para JavaScript

# Adicione esta importação para trabalhar com datas de forma mais robusta
from dateutil.relativedelta import relativedelta
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect


from django.contrib.auth.decorators import login_required
from django.views import View
from .models import CATEGORIA_CHOICES, SUBCATEGORIA_CHOICES, PERIODICIDADE_CHOICES

from datetime import datetime







#  ================================================================
# FUNÇÕES AUXILIARES
# ================================================================

def get_month_range(date_obj):
    """Retorna o primeiro e último dia do mês para uma dada data."""
    first_day = date_obj.replace(day=1)
    last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)
    return first_day, last_day

def calculate_percentage_change(current, previous):
    """Calcula a variação percentual entre dois valores."""
    if previous == 0:
        return 0 if current == 0 else 100
    return ((current - previous) / previous) * 100

def get_sum(queryset):
    """Retorna a soma de 'valor' de um queryset como Decimal, ou 0.00 se vazio."""
    result = queryset.aggregate(total=Sum('valor'))['total']
    return Decimal(str(result)) if result is not None else Decimal('0.00')

# Função para converter Decimals e Dates para tipos serializáveis em JSON
def serialize_for_json(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_for_json(elem) for elem in obj]
    return obj



# ================================================================
# VIEWS DA APLICAÇÃO
# ================================================================

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


def custom_logout(request):
    """View personalizada para logout com mensagem"""
    logout(request)
    messages.success(request, 'Logout realizado com sucesso!')
    return redirect('core:login')

# ================================================================
# VIEWS DE DASHBOARD
# ================================================================
@login_required
def dashboard(request):
    user = request.user
    hoje = dj_timezone.now().date() 
    primeiro_dia_mes_atual, ultimo_dia_mes_atual = get_month_range(hoje)

    # Obter o período de filtro e meses meta (para reserva de emergência)
    # Por agora, não estamos usando o 'periodo' para filtrar os dados gerais,
    # mas é mantido para extensibilidade futura.
    periodo = request.GET.get('periodo', '30')
    meses_meta = int(request.GET.get('meses_meta', 6))

    # Definir a data de início para os dados agregados (usado para últimas transações e alguns gráficos)
    # Para consistência, usaremos um período maior para gráficos de histórico.
    data_inicio_filtro = hoje - timedelta(days=365) # Exemplo: buscar dados do último ano para histórico

    # ================================================================
    # 1. DADOS PRINCIPAIS PARA OS CARDS
    # ================================================================

    saldo_total = ContaBancaria.objects.filter(proprietario=user).aggregate(Sum('saldo_atual'))['saldo_atual__sum'] or Decimal('0.00')

    # Receitas e Despesas do Mês Atual
    entradas_mes_atual = Entrada.objects.filter(
        conta_bancaria__proprietario=user,
        data__range=(primeiro_dia_mes_atual, ultimo_dia_mes_atual)
    ).aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

    saidas_mes_atual = Saida.objects.filter(
        conta_bancaria__proprietario=user,
        data_lancamento__range=(primeiro_dia_mes_atual, ultimo_dia_mes_atual)
    ).aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

    # Receitas e Despesas do Mês Anterior para Variação
    primeiro_dia_mes_anterior = primeiro_dia_mes_atual - relativedelta(months=1)
    ultimo_dia_mes_anterior = (primeiro_dia_mes_anterior + relativedelta(months=1)) - timedelta(days=1)

    entradas_mes_anterior = Entrada.objects.filter(
        conta_bancaria__proprietario=user,
        data__range=(primeiro_dia_mes_anterior, ultimo_dia_mes_anterior)
    ).aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

    saidas_mes_anterior = Saida.objects.filter(
        conta_bancaria__proprietario=user,
        data_lancamento__range=(primeiro_dia_mes_anterior, ultimo_dia_mes_anterior)
    ).aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

    variacao_receitas = calculate_percentage_change(float(entradas_mes_atual), float(entradas_mes_anterior))
    variacao_despesas = calculate_percentage_change(float(saidas_mes_atual), float(saidas_mes_anterior))

    # Reserva de Emergência (Saldo em contas tipo 'poupanca')
    saldo_poupancas = ContaBancaria.objects.filter(
        proprietario=user,
        tipo='poupanca',
        ativa=True
    ).aggregate(Sum('saldo_atual'))['saldo_atual__sum'] or Decimal('0.00')

    # Despesa mensal média (calcula média dos últimos 6 meses para reserva)
    data_seis_meses_atras = hoje - relativedelta(months=6)
    despesas_ultimos_6_meses = Saida.objects.filter(
        conta_bancaria__proprietario=user,
        data_lancamento__gte=data_seis_meses_atras,
        data_lancamento__lte=hoje
    ).aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

    despesa_mensal_media = float(despesas_ultimos_6_meses) / 6 if despesas_ultimos_6_meses else 0

    # ================================================================
    # 2. DADOS PARA GRÁFICOS (Últimos 12 meses para histórico mais completo)
    # ================================================================
    num_meses_historico = 12
    meses_labels = []
    entradas_por_mes_data = []
    saidas_por_mes_data = []
    saldo_acumulado_data = []
    
    # Calcular saldo acumulado histórico
    temp_saldo_acumulado_base = float(saldo_total) # Saldo atual como base
    
    # Para calcular o saldo inicial do período, somamos as saídas e subtraímos as entradas do período para trás
    # Este é um cálculo mais complexo para um saldo "real" no início de cada mês no histórico
    # Para simplificar e focar nos gráficos, vamos pegar o saldo_total e ajustar para trás para cada mês

    for i in range(num_meses_historico - 1, -1, -1): # Começa do mês mais antigo para o atual
        data_mes = hoje - relativedelta(months=i)
        primeiro_dia, ultimo_dia = get_month_range(data_mes)
        
        entradas_mes = Entrada.objects.filter(
            conta_bancaria__proprietario=user,
            data__range=(primeiro_dia, ultimo_dia)
        ).aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

        saidas_mes = Saida.objects.filter(
            conta_bancaria__proprietario=user,
            data_lancamento__range=(primeiro_dia, ultimo_dia)
        ).aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
        
        meses_labels.append(data_mes.strftime('%b/%y'))
        entradas_por_mes_data.append(float(entradas_mes))
        saidas_por_mes_data.append(float(saidas_mes))

        # Calcula o saldo para este mês (saldo do fim do mês anterior + entradas - saídas)
        # Para o saldo acumulado, vamos simular começando com o saldo atual e ajustando para trás
        if i == 0: # Mês atual
            saldo_acumulado_data.append(float(saldo_total))
        else:
            # Saldo acumulado do mês anterior = Saldo acumulado do mês atual - (entradas do mês atual - saídas do mês atual)
            # Ao construir de trás para frente, o primeiro elemento adicionado será o mais antigo, então o append está ok
            # No final, faremos um reverse
            saldo_para_este_mes = temp_saldo_acumulado_base - (float(entradas_mes) - float(saidas_mes))
            saldo_acumulado_data.append(saldo_para_este_mes)
            temp_saldo_acumulado_base = saldo_para_este_mes
    
    # Ajusta os dados para ordem cronológica (do mês mais antigo para o mais novo)
    meses_labels.reverse()
    entradas_por_mes_data.reverse()
    saidas_por_mes_data.reverse()
    saldo_acumulado_data.reverse()

    # ================================================================
    # 3. SAZONALIDADE (Saldo Líquido Mensal)
    # ================================================================
    sazonalidade_labels = meses_labels
    sazonalidade_values = [e - s for e, s in zip(entradas_por_mes_data, saidas_por_mes_data)]

    # ================================================================
    # 4. PROJEÇÃO FUTURA (Regressão Linear Simples)
    # Considera os últimos 6 meses para a projeção, ou menos se não houver dados.
    # ================================================================
    num_meses_projecao = 6 # Projeta 6 meses à frente
    
    # Usar os últimos N meses de dados para a regressão
    data_para_regressao_saldo = saldo_acumulado_data[-num_meses_historico:]
    data_para_regressao_receitas = entradas_por_mes_data[-num_meses_historico:]
    data_para_regressao_despesas = saidas_por_mes_data[-num_meses_historico:]
    
    projecao_labels = meses_labels.copy()
    projecao_saldo_data = saldo_acumulado_data.copy()
    projecao_receitas_data = entradas_por_mes_data.copy()
    projecao_despesas_data = saidas_por_mes_data.copy()

    if len(data_para_regressao_saldo) >= 3: # Mínimo de 3 pontos para regressão significativa
        try:
            X_hist = np.array(range(len(data_para_regressao_saldo))).reshape(-1, 1)
            y_hist_saldo = np.array(data_para_regressao_saldo)
            y_hist_receitas = np.array(data_para_regressao_receitas)
            y_hist_despesas = np.array(data_para_regressao_despesas)

            model_saldo = LinearRegression().fit(X_hist, y_hist_saldo)
            model_receitas = LinearRegression().fit(X_hist, y_hist_receitas)
            model_despesas = LinearRegression().fit(X_hist, y_hist_despesas)

            # Projeta 'num_meses_projecao' meses à frente
            X_fut = np.array(range(len(data_para_regressao_saldo), len(data_para_regressao_saldo) + num_meses_projecao)).reshape(-1, 1)
            
            projecao_saldo_futuro = model_saldo.predict(X_fut)
            projecao_receitas_futuro = model_receitas.predict(X_fut)
            projecao_despesas_futuro = model_despesas.predict(X_fut)

            for i in range(num_meses_projecao):
                next_month = hoje + relativedelta(months=i+1)
                projecao_labels.append(next_month.strftime('%b/%y'))
                projecao_saldo_data.append(float(projecao_saldo_futuro[i]))
                projecao_receitas_data.append(float(projecao_receitas_futuro[i]))
                projecao_despesas_data.append(float(projecao_despesas_futuro[i]))
        except Exception as e:
            # Fallback se a regressão falhar (e.g., dados insuficientes, erro matemático)
            print(f"Erro na projeção de regressão linear: {e}")
            pass # Continua sem projeção se houver erro

    # ================================================================
    # 5. DESPESAS POR CATEGORIA (Mês atual)
    # ================================================================
    saidas_por_categoria = Saida.objects.filter(
        conta_bancaria__proprietario=user,
        data_lancamento__range=(primeiro_dia_mes_atual, ultimo_dia_mes_atual)
    ).values('categoria').annotate(total=Sum('valor')).order_by('categoria')

    # Mapeia os códigos das categorias para seus nomes de exibição
    mapa_categorias_saida_display = {c[0]: c[1] for c in CATEGORIA_CHOICES}
    categorias_despesas_labels = [mapa_categorias_saida_display.get(item['categoria'], item['categoria']) for item in saidas_por_categoria]
    categorias_despesas_data = [float(item['total']) for item in saidas_por_categoria]

    # ================================================================
    # 6. RECEITAS POR CATEGORIA/TIPO (Considera 'forma_recebimento' como categoria para fins de gráfico)
    # ================================================================
    entradas_por_forma = Entrada.objects.filter(
        conta_bancaria__proprietario=user,
        data__range=(primeiro_dia_mes_atual, ultimo_dia_mes_atual)
    ).values('forma_recebimento').annotate(total=Sum('valor')).order_by('forma_recebimento')

    mapa_formas_recebimento_display = {fr[0]: fr[1] for fr in FORMA_RECEBIMENTO_CHOICES}
    categorias_receitas_labels = [mapa_formas_recebimento_display.get(item['forma_recebimento'], item['forma_recebimento']) for item in entradas_por_forma]
    categorias_receitas_values = [float(item['total']) for item in entradas_por_forma]


    # ================================================================
    # 7. SALDOS POR CONTA BANCÁRIA
    # ================================================================
    contas_ativas = ContaBancaria.objects.filter(proprietario=user, ativa=True)
    saldo_contas_labels = []
    saldo_contas_values = []
    
    for conta in contas_ativas:
        # Calcular o saldo "real" da conta (saldo inicial + entradas - saídas)
        entradas_na_conta = Entrada.objects.filter(
            conta_bancaria=conta,
            data__range=(hoje.replace(day=1), hoje) # Entradas do mês atual
        ).aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

        saidas_na_conta = Saida.objects.filter(
            conta_bancaria=conta,
            data_lancamento__range=(hoje.replace(day=1), hoje) # Saídas do mês atual
        ).aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

        saldo_atual_conta = (conta.saldo_atual or Decimal('0.00')) + entradas_na_conta - saidas_na_conta
        
        # Ajuste para cartão de crédito: o saldo_atual da conta de crédito é o limite disponível
        # Se for cartão de crédito, o valor na tela deve ser a fatura atual (ou o que foi gasto)
        if conta.tipo == 'credito':
            # Considerando que 'saldo_atual' para cartões de crédito pode representar o limite
            # Ou, se for '0.00' representa que ainda não foi usado.
            # Para o dashboard, talvez o mais interessante seja o "uso do limite" ou "dívida"
            # Aqui, vou mostrar o saldo atual da conta (que deve ser o limite disponível)
            # ou o gasto se `saldo_atual` for usado para isso
            saldo_contas_values.append(float(conta.limite_cartao - saidas_na_conta) if conta.limite_cartao else float(-saidas_na_conta))
        else:
            saldo_contas_values.append(float(saldo_atual_conta))
        
        saldo_contas_labels.append(f"{conta.get_nome_banco_display()} ({conta.get_tipo_display()})")

    # ================================================================
    # 8. DESPESAS FIXAS VS VARIÁVEIS (Mês atual)
    # ================================================================
    despesas_fixas = Saida.objects.filter(
        conta_bancaria__proprietario=user,
        data_lancamento__range=(primeiro_dia_mes_atual, ultimo_dia_mes_atual),
        recorrente__in=['mensal', 'anual']
    ).aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

    despesas_variaveis = Saida.objects.filter(
        conta_bancaria__proprietario=user,
        data_lancamento__range=(primeiro_dia_mes_atual, ultimo_dia_mes_atual)
    ).exclude(recorrente__in=['mensal', 'anual']).aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

    # ================================================================
    # 9. STATUS DE PAGAMENTOS (Mês atual)
    # ================================================================
    pagos_total = Saida.objects.filter(
        conta_bancaria__proprietario=user,
        data_vencimento__range=(primeiro_dia_mes_atual, ultimo_dia_mes_atual),
        situacao='pago'
    ).aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

    pendentes_total = Saida.objects.filter(
        conta_bancaria__proprietario=user,
        data_vencimento__range=(primeiro_dia_mes_atual, ultimo_dia_mes_atual),
        situacao='pendente'
    ).aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

    # ================================================================
    # 10. ANÁLISE COMPORTAMENTAL
    # ================================================================
    gastos_por_dia_semana_raw = {'Seg': Decimal('0.00'), 'Ter': Decimal('0.00'), 'Qua': Decimal('0.00'), 'Qui': Decimal('0.00'), 'Sex': Decimal('0.00'), 'Sáb': Decimal('0.00'), 'Dom': Decimal('0.00')}
    data_30_dias_atras = hoje - timedelta(days=29)
    saidas_ultimos_30_dias = Saida.objects.filter(
        conta_bancaria__proprietario=user,
        data_lancamento__range=(data_30_dias_atras, hoje)
    )
    
    dias_da_semana_map = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
    
    for saida in saidas_ultimos_30_dias:
        dia_semana_idx = saida.data_lancamento.weekday() # 0 para Segunda, 6 para Domingo
        dia_semana_label = dias_da_semana_map[dia_semana_idx]
        gastos_por_dia_semana_raw[dia_semana_label] += saida.valor

    gastos_por_dia_semana = {k: float(v) for k,v in gastos_por_dia_semana_raw.items()}

    # Gastos por hora do dia (simplificado para demonstração)
    gastos_por_hora_dia_raw = {str(h): Decimal('0.00') for h in range(24)}
    for saida in saidas_ultimos_30_dias:
        # Apenas se a data_lancamento for um datetime, ou usar um valor padrão para hora
        if isinstance(saida.data_lancamento, datetime):
            hora = saida.data_lancamento.hour
        else:
            # Se data_lancamento é um date, vamos usar uma hora arbitrária para agregação ou ignorar
            # Para este exemplo, vou simular uma distribuição uniforme
            hora = saida.data_lancamento.day % 24 # Apenas para ter uma distribuição
        gastos_por_hora_dia_raw[str(hora)] += saida.valor

    gastos_por_hora_dia = {k: float(v) for k,v in gastos_por_hora_dia_raw.items()}


    # Categorias comportamentais simplificadas (necessita de categorização no modelo Saida para ser mais preciso)
    # Para este exemplo, usaremos uma divisão arbitrária.
    total_despesas_mes = float(saidas_mes_atual)
    categorias_comportamento_data = {
        'Essenciais': total_despesas_mes * 0.6,  # Estimativa
        'Supérfluos': total_despesas_mes * 0.3,  # Estimativa
        'Investimentos': total_despesas_mes * 0.1 # Estimativa (ou 0 se não houver investimento direto)
    }

    # ================================================================
    # 11. INDICADORES DE SAÚDE FINANCEIRA
    # ================================================================
    liquidez_corrente = (float(saldo_total) / float(saidas_mes_atual) * 100) if saidas_mes_atual else 0
    margem_seguranca = ((float(entradas_mes_atual) - float(saidas_mes_atual)) / float(entradas_mes_atual) * 100) if entradas_mes_atual else 0
    
    # Dívidas (ex: saldo negativo de cartões de crédito, empréstimos)
    # Assumindo que o saldo_atual negativo em contas de crédito representa dívida
    dividas = ContaBancaria.objects.filter(
        proprietario=user,
        tipo='credito',
    ).aggregate(Sum('saldo_atual'))['saldo_atual__sum'] or Decimal('0.00')
    
    # Soma de todas as despesas a pagar no cartão para o mês atual
    gastos_cartao_mes_atual = Saida.objects.filter(
        conta_bancaria__proprietario=user,
        conta_bancaria__tipo='credito',
        data_vencimento__range=(primeiro_dia_mes_atual, ultimo_dia_mes_atual)
    ).aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

    limite_total_credito = ContaBancaria.objects.filter(
        proprietario=user,
        tipo='credito'
    ).aggregate(Sum('limite_cartao'))['limite_cartao__sum'] or Decimal('0.00')

    # Endividamento: % de gastos_cartao_mes_atual em relação ao limite_total_credito
    endividamento = (float(gastos_cartao_mes_atual) / float(limite_total_credito) * 100) if limite_total_credito > 0 else 0
    
    poupanca_mensal_estimada = float(entradas_mes_atual) - float(saidas_mes_atual)
    reserva_emergencia_ideal_indicador = despesa_mensal_media * meses_meta

    nivel_risco_texto = "Baixo"
    if endividamento > 50: 
        nivel_risco_texto = "Alto"
    elif endividamento > 20: 
        nivel_risco_texto = "Moderado"

    # ================================================================
    # 12. SIMULAÇÕES DE CENÁRIOS
    # ================================================================
    aumento_10_despesas = float(saidas_mes_atual) * 1.10
    reducao_10_despesas = float(saidas_mes_atual) * 0.90
    aumento_10_receitas = float(entradas_mes_atual) * 1.10
    reducao_10_receitas = float(entradas_mes_atual) * 0.90
    impacto_inflacao_5 = float(saidas_mes_atual) * 1.05

    # ================================================================
    # 13. ANÁLISE DE RISCOS
    # ================================================================
    concentracao_risco = 0 # Requer categorização de entradas para cálculo preciso

    # ================================================================
    # 14. OTIMIZAÇÃO DE INVESTIMENTOS
    # ================================================================
    alocacao_investimentos_labels = ['Reserva Emergencial', 'Renda Fixa', 'Renda Variável']
    alocacao_investimentos_values = [70, 20, 10] # Valores de exemplo
    sugestao_investimentos = "Priorize a construção da reserva de emergência."
    if float(saldo_poupancas) >= reserva_emergencia_ideal_indicador:
        sugestao_investimentos = "Sua reserva está completa! Considere diversificar seus investimentos."

    # ================================================================
    # 15. ÚLTIMAS TRANSAÇÕES
    # ================================================================
    ultimas_entradas = Entrada.objects.filter(
        conta_bancaria__proprietario=user
    ).order_by('-data')[:5]

    ultimas_saidas = Saida.objects.filter(
        conta_bancaria__proprietario=user
    ).order_by('-data_lancamento')[:5]

    ultimas_transacoes_list = []
    for entrada in ultimas_entradas:
        ultimas_transacoes_list.append({
            'data': entrada.data.isoformat(),
            'descricao': entrada.nome,
            'valor': float(entrada.valor),
            'tipo': 'Entrada'
        })
    for saida in ultimas_saidas:
        ultimas_transacoes_list.append({
            'data': saida.data_lancamento.isoformat(),
            'descricao': saida.nome,
            'valor': float(-saida.valor), # Despesas são negativas
            'tipo': 'Saída'
        })
    
    ultimas_transacoes_list.sort(key=lambda x: x['data'], reverse=True)
    ultimas_transacoes_list = ultimas_transacoes_list[:10]

    # ================================================================
    # CONSTRUÇÃO DO CONTEXTO A SER PASSADO PARA JSON
    # ================================================================
    context_data = {
        'saldo_geral': float(saldo_total),
        'entradas_mes': float(entradas_mes_atual),
        'saidas_mes': float(saidas_mes_atual),
        'variacao_receitas': variacao_receitas,
        'variacao_despesas': variacao_despesas,
        
        'despesa_mensal_media': despesa_mensal_media,
        'saldo_poupancas': float(saldo_poupancas),
        'meses_meta': meses_meta,

        'indicadores': {
            'liquidez_corrente': liquidez_corrente,
            'margem_seguranca': margem_seguranca,
            'endividamento': endividamento,
            'poupanca_mensal': poupanca_mensal_estimada,
            'reserva_emergencia_ideal': reserva_emergencia_ideal_indicador,
        },

        'analise_comportamental': {
            'gastos_por_dia': gastos_por_dia_semana,
            'gastos_por_hora_dia': gastos_por_hora_dia,
            'categorias_comportamento': categorias_comportamento_data
        },

        'simulacoes': {
            'aumento_10_despesas': aumento_10_despesas,
            'reducao_10_despesas': reducao_10_despesas,
            'aumento_10_receitas': aumento_10_receitas,
            'reducao_10_receitas': reducao_10_receitas,
            'impacto_inflacao_5': impacto_inflacao_5
        },
        
        'analise_riscos': {
            'concentracao_risco': concentracao_risco,
            'reserva_ideal': reserva_emergencia_ideal_indicador,
            'nivel_risco': nivel_risco_texto
        },

        'otimizacao_investimentos': {
            'sugestao': sugestao_investimentos,
            'alocacao_labels': alocacao_investimentos_labels,
            'alocacao_values': alocacao_investimentos_values,
        },

        'ultimas_transacoes': ultimas_transacoes_list,

        'meses_labels': meses_labels,
        'receitas_mensais_data': entradas_por_mes_data,
        'despesas_mensais_data': saidas_por_mes_data,
        'saldo_acumulado_data': saldo_acumulado_data,
        'sazonalidade_labels': sazonalidade_labels,
        'sazonalidade_values': sazonalidade_values,
        
        'projecao_labels': projecao_labels,
        'projecao_receitas': projecao_receitas_data,
        'projecao_despesas': projecao_despesas_data,
        'projecao_saldo': projecao_saldo_data,

        'categorias_despesas_labels': categorias_despesas_labels,
        'categorias_despesas_data': categorias_despesas_data,
        'categorias_receitas_labels': categorias_receitas_labels,
        'categorias_receitas_values': categorias_receitas_values,
        
        'saldo_contas_labels': saldo_contas_labels,
        'saldo_contas_values': saldo_contas_values,
        
        'despesas_fixas': float(despesas_fixas),
        'despesas_variaveis': float(despesas_variaveis),

        'pagos_total': float(pagos_total),
        'pendentes_total': float(pendentes_total),
    }

    # Serializa todos os dados para JSON, usando a função auxiliar para Decimals e Dates
    dados_graficos_json = json.dumps(context_data, default=serialize_for_json)
    
    context = {'dados_graficos_json': dados_graficos_json}
    
    return render(request, 'core/dashboard.html', context)


# ===== FUNÇÃO AUXILIAR ÚNICA =====
def get_sum(queryset):
    """Retorna a soma de 'valor' de um queryset como Decimal, ou 0.00 se vazio."""
    result = queryset.aggregate(total=Sum('valor'))['total']
    return Decimal(str(result)) if result is not None else Decimal('0.00')

# ===== FUNÇÕES ADICIONAIS =====
def get_contas_bancarias_data(usuario):
    """Retorna dados das contas bancárias para gráficos"""
    contas = ContaBancaria.objects.filter(proprietario=usuario, ativa=True)
    labels = [str(conta) for conta in contas]
    data = []
    
    for conta in contas:
        total_despesas = get_sum(Saida.objects.filter(usuario=usuario, conta_bancaria=conta))
        total_receitas = get_sum(Entrada.objects.filter(usuario=usuario, conta_bancaria=conta))
        saldo = float(total_receitas - total_despesas + (conta.saldo_atual or Decimal('0.00')))
        data.append(saldo)
    
    return {'labels': labels, 'data': data}

def get_saldos_contas(usuario):
    """Retorna saldos de todas as contas do usuário"""
    contas = ContaBancaria.objects.filter(proprietario=usuario)
    saldos = {}
    
    for conta in contas:
        try:
            entradas = get_sum(Entrada.objects.filter(usuario=usuario, conta_bancaria=conta))
            saidas = get_sum(Saida.objects.filter(usuario=usuario, conta_bancaria=conta))
            
            if conta.tipo == 'credito':
                saldo = (conta.saldo_atual or Decimal('0.00')) - saidas
            else:
                saldo = (conta.saldo_atual or Decimal('0.00')) + entradas - saidas
            
            saldos[conta.id] = {
                'nome': f"{conta.get_nome_banco_display()} - {conta.agencia}-{conta.numero_conta}",
                'saldo': float(saldo),
                'tipo': conta.get_tipo_display()
            }
            
        except Exception as e:
            saldos[conta.id] = {
                'nome': f"{conta.get_nome_banco_display()} - {conta.agencia}-{conta.numero_conta}",
                'saldo': 0.0,
                'tipo': conta.get_tipo_display(),
                'erro': str(e)
            }
    
    return saldos

# Opcional: Quebrar em funções auxiliares dentro da mesma view
def _calcular_dados_mensais(usuario, data_inicio, data_fim):
    """Calcula entradas e saídas para um período"""
    entradas = Entrada.objects.filter(
        conta_bancaria__proprietario=usuario,
        data_lancamento__range=(data_inicio, data_fim)
    ).aggregate(Sum('valor'))['valor__sum'] or 0
    
    saidas = Saida.objects.filter(
        conta_bancaria__proprietario=usuario,
        data_lancamento__range=(data_inicio, data_fim)
    ).aggregate(Sum('valor'))['valor__sum'] or 0
    
    return float(entradas), float(saidas)

# ===== VIEWS HTTP =====
@login_required
@require_GET
def get_account_balance(request, pk):
    """Retorna saldo de conta específica via AJAX"""
    try:
        conta = get_object_or_404(ContaBancaria, pk=pk, proprietario=request.user)
        return JsonResponse({'success': True, 'saldo': float(conta.saldo_atual or 0)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)




# ================================================================
# VIEWS DE CONTAS BANCÁRIAS
# ================================================================

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


# ================================================================
# VIEWS DE ENTRADAS
# ================================================================



@login_required
def entrada_list(request):
    # Lista de meses para o filtro
    meses_choices = [
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
    mes_filtro = request.GET.get('mes', str(mes_atual).zfill(2))  # Garantir 2 dígitos
    conta_filter_id = request.GET.get('conta') # Novo filtro de conta
    forma_recebimento_filter_code = request.GET.get('forma_recebimento') # Novo filtro de forma de recebimento

    # Validar ano_filtro
    try:
        ano_filtro = int(ano_filtro)
    except (ValueError, TypeError):
        ano_filtro = ano_atual
    
    # Validar mes_filtro
    if mes_filtro == 'todos':
        mes_num = None
    else:
        try:
            mes_num = int(mes_filtro)
            if mes_num < 1 or mes_num > 12:
                mes_num = mes_atual
        except (ValueError, TypeError):
            mes_num = mes_atual
    
    # Aplica os filtros
    entradas = Entrada.objects.filter(usuario=request.user)
    
    # Sempre filtra pelo ano selecionado
    entradas = entradas.filter(data__year=ano_filtro)
    
    # Se tem filtro de mês específico (não é 'todos')
    if mes_num:
        entradas = entradas.filter(data__month=mes_num)
        mes_selecionado = str(mes_num).zfill(2)
    else:
        mes_selecionado = 'todos'
    
    if conta_filter_id:
        entradas = entradas.filter(conta_bancaria__pk=conta_filter_id)
    
    if forma_recebimento_filter_code:
        entradas = entradas.filter(forma_recebimento=forma_recebimento_filter_code)
    
    # Cálculos para os cards
    total_filtrado = entradas.aggregate(total=Sum('valor'))['total'] or 0
    
    # Para cálculo da variação mensal (só faz sentido se estiver filtrando por mês específico)
    if mes_num:
        mes_anterior = mes_num - 1 if mes_num > 1 else 12
        ano_mes_anterior = ano_filtro if mes_num > 1 else ano_filtro - 1
        
        # Entradas do mês anterior para comparação
        entradas_mes_anterior = Entrada.objects.filter(
            usuario=request.user,
            data__month=mes_anterior,
            data__year=ano_mes_anterior
        ).aggregate(total=Sum('valor'))['total'] or 0
        
        if entradas_mes_anterior > 0:
            variacao_mensal = round(((total_filtrado - entradas_mes_anterior) / entradas_mes_anterior * 100), 2)
        else:
            variacao_mensal = 100 if total_filtrado > 0 else 0
    else:
        # Se está visualizando "todos" os meses, não calcula variação
        variacao_mensal = 0
    
    # Média mensal (considera todos os meses com registros)
    total_meses = Entrada.objects.filter(usuario=request.user).dates('data', 'month').count()
    total_geral = Entrada.objects.filter(usuario=request.user).aggregate(total=Sum('valor'))['total'] or 0
    media_mensal = round((total_geral / total_meses) if total_meses > 0 else 0, 2)
    
    # Nome do mês para o título
    if mes_num:
        mes_nome = dict(meses_choices).get(mes_num, '')
    else:
        mes_nome = f'Todos os meses de {ano_filtro}'
    
    # Obter contas bancárias para os selects de filtro e modal
    contas_bancarias_filter_qs = ContaBancaria.objects.filter(proprietario=request.user, ativa=True)
    
    # Criar mapas para exibir os nomes nos badges
    contas_bancarias_display_map = {str(c.pk): c.get_nome_banco_display() for c in contas_bancarias_filter_qs}
    meses_disponiveis_display_map = {str(k).zfill(2): v for k, v in meses_choices}
    forma_recebimento_choices_map = {str(k): v for k, v in FORMA_RECEBIMENTO_CHOICES}


    # Gerar lista de anos (2 anos atrás, atual, 1 ano à frente)
    anos_disponiveis = sorted(list(set(
        list(Entrada.objects.filter(usuario=request.user).values_list('data__year', flat=True)) +
        list(range(ano_atual - 2, ano_atual + 2))
    )), reverse=True)
    
    return render(request, 'core/entrada_list.html', {
        'entradas': entradas.order_by('-data'),
        'meses_disponiveis': meses_choices, # Para o select de filtro
        'anos_disponiveis': anos_disponiveis,
        'conta_filter': conta_filter_id, # Passa o ID da conta filtrada
        'mes_filter': mes_selecionado, # Passa o mês filtrado (string de 2 dígitos ou 'todos')
        'ano_filter': str(ano_filtro), # Passa o ano filtrado (string)
        'forma_recebimento_filter': forma_recebimento_filter_code, # Passa o código da forma de recebimento filtrada
        'total_entradas': total_filtrado,
        'entradas_mes_atual': total_filtrado,
        'media_mensal': media_mensal,
        'variacao_mensal': variacao_mensal,
        'mes_atual_nome': mes_nome,
        'ano_atual': ano_filtro,  # Usar o ano filtrado, não necessariamente o atual
        'FORMA_RECEBIMENTO_CHOICES': FORMA_RECEBIMENTO_CHOICES, # Para o select de filtro do modal e filtro principal
        'contas_bancarias': contas_bancarias_filter_qs, # Para o select do modal
        'contas_bancarias_filter': contas_bancarias_filter_qs, # Para o select de filtro principal
        'mes_atual_num': str(mes_atual).zfill(2),  # Para uso no template
        'contas_bancarias_display_map': contas_bancarias_display_map, # Para os badges
        'meses_disponiveis_display_map': meses_disponiveis_display_map, # Para os badges
        'FORMA_RECEBIMENTO_CHOICES_MAP': forma_recebimento_choices_map, # Para os badges
    })

@login_required
def entrada_create(request):
    if request.method == 'POST':
        form = EntradaForm(request.POST, user=request.user)
        if form.is_valid():
            entrada = form.save(commit=False)
            entrada.usuario = request.user
            entrada.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Entrada criada com sucesso!'})
            else:
                messages.success(request, 'Entrada criada com sucesso!')
                return redirect('core:entrada_list')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = EntradaForm(user=request.user)
    
    # Obter contas bancárias do usuário
    contas_bancarias = ContaBancaria.objects.filter(proprietario=request.user, ativa=True)
    
    # Se for requisição AJAX (modal), retornar JSON com os dados necessários
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        contas_data = [{'id': conta.id, 'nome': conta.get_nome_banco_display()} for conta in contas_bancarias]
        
        return JsonResponse({
            'form_html': render_to_string('core/includes/entrada_form_modal.html', {
                'form': form,
                'FORMA_RECEBIMENTO_CHOICES': FORMA_RECEBIMENTO_CHOICES,
                'contas_bancarias': contas_bancarias
            }, request=request)
        })
    
    # Se for requisição normal, renderizar a página completa
    return render(request, 'core/entrada_form.html', {
        'form': form,
        'action': 'Criar',
        'FORMA_RECEBIMENTO_CHOICES': FORMA_RECEBIMENTO_CHOICES,
        'contas_bancarias': contas_bancarias
    })

@login_required
def entrada_update(request, pk):
    entrada = get_object_or_404(Entrada, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        form = EntradaForm(request.POST, instance=entrada, user=request.user)
        if form.is_valid():
            form.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Entrada atualizada com sucesso!'})
            else:
                messages.success(request, 'Entrada atualizada com sucesso!')
                return redirect('core:entrada_list')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            else:
                messages.error(request, 'Erro ao atualizar a entrada. Verifique os campos.')
    
    else:
        form = EntradaForm(instance=entrada, user=request.user)
    
    # Obter contas bancárias do usuário
    contas_bancarias = ContaBancaria.objects.filter(proprietario=request.user, ativa=True)
    
    # Se for requisição AJAX (modal), retornar JSON com os dados necessários
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'form_html': render_to_string('core/includes/entrada_form_modal.html', {
                'form': form,
                'FORMA_RECEBIMENTO_CHOICES': FORMA_RECEBIMENTO_CHOICES,
                'contas_bancarias': contas_bancarias
            }, request=request)
        })
    
    return render(request, 'core/entrada_form.html', {
        'form': form,
        'action': 'Atualizar',
        'FORMA_RECEBIMENTO_CHOICES': FORMA_RECEBIMENTO_CHOICES,
        'contas_bancarias': contas_bancarias
    })

@login_required
def entrada_delete(request, pk):
    entrada = get_object_or_404(Entrada, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        entrada.delete()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Entrada excluída com sucesso!'})
        
        messages.success(request, 'Entrada excluída com sucesso!')
        return redirect('core:entrada_list')
    
    # Se for GET e AJAX, retornar informações para o modal de confirmação
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'entrada_nome': entrada.nome,
            'entrada_valor': str(entrada.valor),
            'entrada_data': entrada.data.strftime('%d/%m/%Y')
        })
    
    # Se for GET tradicional, retornar o template de confirmação
    return render(request, 'core/entrada_confirm_delete.html', {'entrada': entrada})


# ================================================================
# VIEWS DE SAÍDAS
# ================================================================

@login_required
def saida_list(request):
    meses_choices = [
        ('01', 'Janeiro'), ('02', 'Fevereiro'), ('03', 'Março'), ('04', 'Abril'),
        ('05', 'Maio'), ('06', 'Junho'), ('07', 'Julho'), ('08', 'Agosto'),
        ('09', 'Setembro'), ('10', 'Outubro'), ('11', 'Novembro'), ('12', 'Dezembro')
    ]
    
    STATUS_CHOICES_DISPLAY = [
        ('pago', 'Pago'),
        ('pendente', 'Pendente')
    ]

    hoje = dj_timezone.now()
    ano_atual = hoje.year
    mes_atual = hoje.month
    
    # Filtros
    ano_filter_str = request.GET.get('ano', str(ano_atual))
    mes_filter_str = request.GET.get('mes', str(mes_atual).zfill(2))
    status_filter_code = request.GET.get('status', '')
    
    # Validar filtros
    try:
        ano_filter = int(ano_filter_str)
    except (ValueError, TypeError):
        ano_filter = ano_atual
    
    if mes_filter_str == '':
        mes_num = None
    else:
        try:
            mes_num = int(mes_filter_str)
            if mes_num < 1 or mes_num > 12:
                mes_num = mes_atual
        except (ValueError, TypeError):
            mes_num = mes_atual
    
    # Aplica os filtros
    saidas_qs = Saida.objects.filter(usuario=request.user)
    saidas_qs = saidas_qs.filter(data_vencimento__year=ano_filter)
    
    if mes_num:
        saidas_qs = saidas_qs.filter(data_vencimento__month=mes_num)
        mes_selecionado = str(mes_num).zfill(2)
    else:
        mes_selecionado = ''
    
    if status_filter_code:
        saidas_qs = saidas_qs.filter(situacao=status_filter_code)
        status_selecionado = status_filter_code
    else:
        status_selecionado = ''
    
    # Processar despesas para exibir no template
    saidas = saidas_qs.order_by('-data_vencimento')
    
    # Cálculos para os cards
    total_despesas = get_sum(saidas_qs)
    despesas_pagas = get_sum(saidas_qs.filter(situacao='pago'))
    despesas_pendentes = get_sum(saidas_qs.filter(situacao='pendente'))
    
    percentual_pago = round((despesas_pagas / total_despesas * 100) if total_despesas > 0 else 0, 2)
    percentual_pendente = round((despesas_pendentes / total_despesas * 100) if total_despesas > 0 else 0, 2)
    
    # Para cálculo da variação mensal
    variacao_mensal = Decimal('0.00')
    variacao_mensal_abs = Decimal('0.00')
    if mes_num:
        mes_anterior_date = hoje - relativedelta(months=1)
        primeiro_dia_mes_anterior, ultimo_dia_mes_anterior = get_month_range(mes_anterior_date)
        
        saidas_mes_anterior_qs = Saida.objects.filter(
            usuario=request.user,
            data_vencimento__range=(primeiro_dia_mes_anterior, ultimo_dia_mes_anterior)
        )
        if status_filter_code:
            saidas_mes_anterior_qs = saidas_mes_anterior_qs.filter(situacao=status_filter_code)

        total_despesas_mes_anterior = get_sum(saidas_mes_anterior_qs)
        
        if total_despesas_mes_anterior > 0:
            variacao_mensal = round(((total_despesas - total_despesas_mes_anterior) / total_despesas_mes_anterior * 100), 2)
        else:
            variacao_mensal = Decimal('100.00') if total_despesas > 0 else Decimal('0.00')
        
        variacao_mensal_abs = abs(variacao_mensal)
    
    # Nome do mês para o título
    mes_nome = dict(meses_choices).get(mes_selecionado, 'Todos os meses')
    if mes_selecionado == '':
        mes_nome = 'Todos os meses'

    # Anos disponíveis
    anos_com_registros = set(Saida.objects.filter(usuario=request.user).values_list('data_vencimento__year', flat=True))
    anos_disponiveis = sorted(list(anos_com_registros.union(range(ano_atual - 2, ano_atual + 2))), reverse=True)

    # Mapeamento de meses e status para badges
    meses_display_map = {k: v for k, v in meses_choices}
    status_display_map = {k: v for k, v in STATUS_CHOICES_DISPLAY}
    
    # CORREÇÃO AQUI: usar request.user em vez de user
    contas_bancarias = ContaBancaria.objects.filter(proprietario=request.user, ativa=True)
    
    form = SaidaForm(user=request.user)
    
    context = {
        'saidas': saidas,
        'total_despesas': total_despesas,
        'despesas_pagas': despesas_pagas,
        'despesas_pendentes': despesas_pendentes,
        'percentual_pago': percentual_pago,
        'percentual_pendente': percentual_pendente,
        'variacao_mensal': variacao_mensal,
        'variacao_mensal_abs': variacao_mensal_abs,
        'mes_atual_nome': mes_nome,
        'ano_atual': ano_filter,
        'meses': meses_choices,
        'anos_disponiveis': anos_disponiveis,
        'STATUS_CHOICES': STATUS_CHOICES_DISPLAY,
        'ano_selecionado': str(ano_filter),
        'mes_selecionado': mes_selecionado,
        'status_selecionado': status_selecionado,
        'meses_display_map': meses_display_map,
        'status_display_map': status_display_map,
        'form': form,
        'today_date': dj_timezone.now().date().isoformat(),
        'contas_bancarias': contas_bancarias,  # Adicione esta linha
        'CATEGORIA_CHOICES': CATEGORIA_CHOICES,  # Adicione esta linha
        'SUBCATEGORIA_CHOICES': SUBCATEGORIA_CHOICES,  # Adicione esta linha
        'FORMA_PAGAMENTO_CHOICES': FORMA_PAGAMENTO_CHOICES,  # Adicione esta linha
        'TIPO_PAGAMENTO_DETALHE_CHOICES': TIPO_PAGAMENTO_DETALHE_CHOICES,  # Adicione esta linha
        'PERIODICIDADE_CHOICES': PERIODICIDADE_CHOICES,  # Adicione esta linha
        'SITUACAO_CHOICES': SITUACAO_CHOICES,  # Adicione esta linha
    }
    
    return render(request, 'core/saida_list.html', context)

from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class MarcarComoPagoView(View):
    def post(self, request, saida_id):
        print(f"DEBUG: saida_id = {saida_id}")
        print(f"DEBUG: request.user = {request.user}")
        
        try:
            saida = Saida.objects.get(id=saida_id, usuario=request.user)
            saida.situacao = 'pago'
            saida.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Despesa marcada como paga com sucesso!'
            })
            
        except Saida.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Despesa não encontrada.'
            }, status=404)
        

def criar_saidas_recorrentes(saida_original):
    """Cria ocorrências futuras para despesas recorrentes"""
    if saida_original.recorrente == 'unica':
        return
    
    from dateutil.relativedelta import relativedelta
    
    # Determinar incremento baseado na periodicidade
    if saida_original.recorrente == 'mensal':
        delta = relativedelta(months=1)
    elif saida_original.recorrente == 'anual':
        delta = relativedelta(years=1)
    else:
        return
    
    # Criar 12 ocorrências futuras (1 ano)
    for i in range(1, 13):
        nova_saida = Saida(
            usuario=saida_original.usuario,
            nome=saida_original.nome,
            valor=saida_original.valor,
            data_lancamento=saida_original.data_lancamento + delta * i,
            data_vencimento=saida_original.data_vencimento + delta * i,
            local=saida_original.local,
            categoria=saida_original.categoria,
            subcategoria=saida_original.subcategoria,
            forma_pagamento=saida_original.forma_pagamento,
            tipo_pagamento_detalhe=saida_original.tipo_pagamento_detalhe,
            situacao='pendente',  # Próximas ocorrências sempre pendentes
            quantidade_parcelas=saida_original.quantidade_parcelas,
            valor_parcela=saida_original.valor_parcela,
            recorrente=saida_original.recorrente,
            observacao=f"{saida_original.observacao or ''} [Recorrente: {i+1}/12]",
            conta_bancaria=saida_original.conta_bancaria
        )
        nova_saida.save()

import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .forms import SaidaForm
# Certifique-se de que criar_saidas_recorrentes esteja importado corretamente
# from .utils import criar_saidas_recorrentes # Exemplo de importação se estiver em um utils.py

# Obtenha uma instância do logger
logger = logging.getLogger(__name__)

import logging
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from decimal import Decimal
import json

from .forms import SaidaForm
from .models import Saida

logger = logging.getLogger(__name__)

def saida_create(request):
    logger.debug("Tentativa de criar nova despesa")
    logger.debug(f"Dados recebidos: {request.POST}")
    
    try:
        # Usar request.POST diretamente para forms Django
        form = SaidaForm(request.POST, user=request.user)
        
        logger.debug(f"Formulário é válido: {form.is_valid()}")
        
        if form.is_valid():
            saida = form.save(commit=False)
            saida.usuario = request.user
            saida.save()
            
            logger.debug(f"Despesa {saida.id} criada com sucesso")
            
            return JsonResponse({
                'success': True, 
                'message': 'Despesa cadastrada com sucesso!',
                'id': saida.id
            })
        else:
            logger.error(f"Erros de validação: {form.errors.as_json()}")
            return JsonResponse({
                'success': False, 
                'errors': form.errors.get_json_data()
            }, status=400)
            
    except Exception as e:
        logger.error(f"Erro ao criar despesa: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False, 
            'message': f'Erro interno do servidor: {str(e)}'
        }, status=500)

@login_required
def saida_update(request, pk):
    saida = get_object_or_404(Saida, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
                
            form = SaidaForm(data, instance=saida, user=request.user)
            
            if form.is_valid():
                saida_atualizada = form.save()
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Despesa atualizada com sucesso!',
                    'id': saida_atualizada.id
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'errors': form.errors
                }, status=400)
                
        except Exception as e:
            logger.error(f"Erro ao atualizar despesa: {str(e)}")
            return JsonResponse({
                'success': False, 
                'message': f'Erro ao atualizar: {str(e)}'
            }, status=500)
    
    # GET request - retornar dados da despesa
    return JsonResponse({
        'success': True,
        'saida': {
            'id': saida.id,
            'nome': saida.nome,
            'valor': str(saida.valor),
            'data_lancamento': saida.data_lancamento.isoformat() if saida.data_lancamento else '',
            'data_vencimento': saida.data_vencimento.isoformat() if saida.data_vencimento else '',
            'local': saida.local or '',
            'categoria': saida.categoria or '',
            'subcategoria': saida.subcategoria or '',
            'forma_pagamento': saida.forma_pagamento or '',
            'tipo_pagamento_detalhe': saida.tipo_pagamento_detalhe or '',
            'situacao': saida.situacao or 'pendente',
            'quantidade_parcelas': saida.quantidade_parcelas or 1,
            'recorrente': saida.recorrente or 'unica',
            'observacao': saida.observacao or '',
            'conta_bancaria': saida.conta_bancaria.id if saida.conta_bancaria else '',
            'valor_parcela': str(saida.valor_parcela) if saida.valor_parcela else '0.00'
        }
    })
# Exemplo de uma função de utilidade para criar saídas recorrentes (ajuste conforme sua implementação)
def criar_saidas_recorrentes(saida_original):
    logger.debug(f"Função criar_saidas_recorrentes chamada para saida ID: {saida_original.id}")
    # Implemente aqui a lógica para criar as saídas recorrentes
    # Você precisará duplicar a despesa original e ajustar datas
    pass # Remova este 'pass' e adicione sua implementação real



@login_required
def saida_delete(request, pk):
    saida = get_object_or_404(Saida, pk=pk, usuario=request.user)

    if request.method == 'POST':
        saida.delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Despesa excluída com sucesso!'})

        messages.success(request, 'Despesa excluída com sucesso!')
        return redirect('core:saida_list')

    # GET request (se acessado diretamente, o que não deve ocorrer com o modal JS)
    # Apenas para garantir que o Django tem um fallback
    return render(request, 'core/saida_confirm_delete.html', {'saida': saida})


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
@require_GET
def get_saida_choices(request):
    """Retorna todas as choices necessárias para o formulário de saída"""
    return JsonResponse({
        'categoria_choices': CATEGORIA_CHOICES,
        'subcategoria_choices': SUBCATEGORIA_CHOICES,
        'forma_pagamento_choices': FORMA_PAGAMENTO_CHOICES,
        'tipo_pagamento_choices': TIPO_PAGAMENTO_DETALHE_CHOICES,
        'periodicidade_choices': PERIODICIDADE_CHOICES,
        'situacao_choices': SITUACAO_CHOICES,
    })  
# ================================================================
# VIEWS DE EXTRATO COMPLETO
# ================================================================

@login_required
def extrato_completo(request):
    meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]
    
    hoje = datetime.now()
    ano_atual = hoje.year
    mes_atual = hoje.month
    
    ano_filtro = request.GET.get('ano', str(ano_atual))
    mes_filtro = request.GET.get('mes', str(mes_atual))
    tipo_filtro = request.GET.get('tipo')
    
    entradas = Entrada.objects.filter(usuario=request.user)
    saidas = Saida.objects.filter(usuario=request.user)
    
    if mes_filtro and mes_filtro != 'todos':
        entradas = entradas.filter(data__month=mes_filtro)
        saidas = saidas.filter(data_vencimento__month=mes_filtro)
    
    entradas = entradas.filter(data__year=ano_filtro)
    saidas = saidas.filter(data_vencimento__year=ano_filtro)
    
    if tipo_filtro == 'entrada':
        saidas = saidas.none()
    elif tipo_filtro == 'saida':
        entradas = entradas.none()
    
    transacoes = sorted(
        list(entradas) + list(saidas),
        key=lambda x: x.data if hasattr(x, 'data') else x.data_vencimento,
        reverse=True
    )
    
    total_entradas = entradas.aggregate(total=Sum('valor'))['total'] or 0
    total_saidas = saidas.aggregate(total=Sum('valor'))['total'] or 0
    saldo_mes = total_entradas - total_saidas
    
    mes_para_calculo = int(mes_filtro) if mes_filtro and mes_filtro != 'todos' else mes_atual
    ano_para_calculo = int(ano_filtro)
    
    mes_anterior = mes_para_calculo - 1 if mes_para_calculo > 1 else 12
    ano_mes_anterior = ano_para_calculo if mes_para_calculo > 1 else ano_para_calculo - 1
    
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
        variacao_mensal = round((saldo_mes - saldo_mes_anterior) / abs(saldo_mes_anterior) * 100, 2)
    else:
        variacao_mensal = 100 if saldo_mes > 0 else 0
    
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

def get_saldo_historico(usuario, meses=12):
    historico_saldo = []
    labels = []
    today = date.today()

    for i in range(meses -1, -1, -1):
        target_date = today - relativedelta(months=i)
        
        first_day_of_month = target_date.replace(day=1)
        last_day_of_month = (first_day_of_month + relativedelta(months=1)) - timedelta(days=1)

        entradas_ate_mes = get_sum(
            Entrada.objects.filter(
                usuario=usuario,
                data__lte=last_day_of_month
            )
        )
        
        saidas_ate_mes = get_sum(
            Saida.objects.filter(
                usuario=usuario,
                data_vencimento__lte=last_day_of_month
            )
        )
        
        saldo_mensal = entradas_ate_mes - saidas_ate_mes
        historico_saldo.append(float(saldo_mensal))
        labels.append(f"{target_date.month:02d}/{target_date.year}")
    
    return labels, historico_saldo

def get_transacoes_recentes(usuario, limite=5):
    ultimas_entradas = Entrada.objects.filter(usuario=usuario).order_by('-data')[:limite]
    ultimas_saidas = Saida.objects.filter(usuario=usuario).order_by('-data_vencimento')[:limite]

    transacoes = sorted(
        list(ultimas_entradas) + list(ultimas_saidas),
        key=lambda x: x.data if hasattr(x, 'data') else x.data_vencimento,
        reverse=True
    )[:limite]

    formatted_transacoes = []
    for t in transacoes:
        if hasattr(t, 'data'):
            formatted_transacoes.append({
                'tipo': 'Entrada',
                'nome': t.nome,
                'valor': float(t.valor),
                'data': t.data.strftime('%d/%m/%Y'),
                'conta': t.conta_bancaria.get_nome_banco_display(),
            })
        else:
            formatted_transacoes.append({
                'tipo': 'Saída',
                'nome': t.nome,
                'valor': float(t.valor),
                'data': t.data_vencimento.strftime('%d/%m/%Y'),
                'conta': t.conta_bancaria.get_nome_banco_display(),
            })
    return formatted_transacoes

def get_saldo_por_tipo_conta(usuario):
    saldo_por_tipo = {}
    
    for tipo_code, tipo_display in ContaBancaria.TIPO_CONTA_CHOICES:
        contas_desse_tipo = ContaBancaria.objects.filter(proprietario=usuario, tipo=tipo_code)
        
        saldo_total_tipo = Decimal('0.00')
        for conta in contas_desse_tipo:
            entradas_conta = get_sum(Entrada.objects.filter(usuario=usuario, conta_bancaria=conta))
            saidas_conta = get_sum(Saida.objects.filter(usuario=usuario, conta_bancaria=conta))
            
            if tipo_code == 'credito':
                saldo_conta = -saidas_conta
            else:
                saldo_conta = (conta.saldo_atual or Decimal('0.00')) + entradas_conta - saidas_conta
            
            saldo_total_tipo += saldo_conta
        
        if saldo_total_tipo != Decimal('0.00'):
            saldo_por_tipo[tipo_display] = float(saldo_total_tipo)
            
    return saldo_por_tipo


def get_entradas_por_forma_recebimento(usuario):
    entradas_por_forma = Entrada.objects.filter(usuario=usuario).values('forma_recebimento').annotate(total=Sum('valor'))

    labels = []
    values = []
    
    for item in entradas_por_forma:
        display_name = next((name for code, name in Entrada.FORMA_RECEBIMENTO_CHOICES if code == item['forma_recebimento']), item['forma_recebimento'])
        labels.append(display_name)
        values.append(float(item['total']))

    return {'labels': labels, 'data': values}


# views.py
from django.http import JsonResponse
from django.template.loader import render_to_string

@login_required
def transacao_detalhes(request, pk):
    try:
        # Tenta encontrar como Entrada primeiro
        try:
            transacao = Entrada.objects.get(pk=pk, usuario=request.user)
            tipo = 'Entrada'
        except Entrada.DoesNotExist:
            transacao = Saida.objects.get(pk=pk, usuario=request.user)
            tipo = 'Saida'
        
        context = {
            'transacao': transacao,
            'tipo': tipo
        }
        
        html = render_to_string('core/includes/transacao_detalhes_modal.html', context, request=request)
        return JsonResponse({'success': True, 'html': html})
        
    except (Entrada.DoesNotExist, Saida.DoesNotExist):
        return JsonResponse({'success': False, 'message': 'Transação não encontrada'})

@login_required
def marcar_como_pago(request, pk):
    try:
        saida = Saida.objects.get(pk=pk, usuario=request.user)
        
        if saida.situacao != 'pago':
            saida.situacao = 'pago'
            saida.data_lancamento = timezone.now().date()
            saida.save()
            
            return JsonResponse({
                'success': True, 
                'message': 'Transação marcada como paga com sucesso!'
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': 'Esta transação já está paga'
            })
            
    except Saida.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Transação não encontrada'})



# ================================================================
# VIEWS DE SALDO ATUAL
# ================================================================


@login_required
def saldo_atual(request):
    try:
        user = request.user
        hoje = date.today()
        
        # Obter contas do usuário
        contas = ContaBancaria.objects.filter(proprietario=user)
        
        # Inicializar variáveis de saldo
        saldo_geral = Decimal('0.00')
        saldo_total_contas_ativas = Decimal('0.00')
        saldo_total_cartoes_credito = Decimal('0.00')
        saldo_total_contas_corrente = Decimal('0.00')
        saldo_total_contas_poupanca = Decimal('0.00')
        saldo_total_investimento = Decimal('0.00')
        total_ativos = Decimal('0.00')
        total_dividas = Decimal('0.00')
        
        # Calcular saldos por conta e agregar totais
        for conta in contas:
            saldo_conta = conta.saldo_atual or Decimal('0.00')
            saldo_geral += saldo_conta
            
            if conta.ativa:
                if conta.tipo == 'credito':
                    saldo_total_cartoes_credito += saldo_conta
                    if saldo_conta < 0:
                        total_dividas += abs(saldo_conta) 
                elif conta.tipo == 'corrente':
                    saldo_total_contas_corrente += saldo_conta
                    if saldo_conta > 0:
                        total_ativos += saldo_conta
                elif conta.tipo == 'poupanca':
                    saldo_total_contas_poupanca += saldo_conta
                    if saldo_conta > 0:
                        total_ativos += saldo_conta
                elif conta.tipo == 'investimento':
                    saldo_total_investimento += saldo_conta
                    if saldo_conta > 0:
                        total_ativos += saldo_conta
                
                saldo_total_contas_ativas += saldo_conta
        
        # Calcular entradas e saídas do mês atual
        primeiro_dia_mes = hoje.replace(day=1)
        proximo_mes = primeiro_dia_mes + relativedelta(months=1)
        ultimo_dia_mes = proximo_mes - timedelta(days=1)
        
        entradas_mes_atual = Entrada.objects.filter(
            conta_bancaria__proprietario=user,
            data__range=(primeiro_dia_mes, ultimo_dia_mes)
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        saidas_mes_atual = Saida.objects.filter(
            conta_bancaria__proprietario=user,
            data_vencimento__range=(primeiro_dia_mes, ultimo_dia_mes)
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        despesas_mes_atual = saidas_mes_atual
        fluxo_mensal = entradas_mes_atual - despesas_mes_atual
        patrimonio_liquido = saldo_geral
        reserva_emergencia = saldo_total_contas_corrente + saldo_total_contas_poupanca + saldo_total_investimento
        
        # Calcular meses de reserva
        despesas_mensais_medias = despesas_mes_atual
        meses_reserva = (reserva_emergencia / despesas_mensais_medias) if despesas_mensais_medias > 0 else Decimal('0.00')
        
        # Calcular taxa de economia
        receitas_mensais_medias = entradas_mes_atual
        taxa_economia = (fluxo_mensal / receitas_mensais_medias * 100) if receitas_mensais_medias > 0 else Decimal('0.00')
        
        # Preparar dados para gráficos de Distribuição do Patrimônio
        distribuicao_labels = []
        distribuicao_values = []
        
        if saldo_total_contas_corrente != 0:
            distribuicao_labels.append('Conta Corrente')
            distribuicao_values.append(float(saldo_total_contas_corrente))
        
        if saldo_total_contas_poupanca != 0:
            distribuicao_labels.append('Poupança')
            distribuicao_values.append(float(saldo_total_contas_poupanca))

        if saldo_total_investimento != 0:
            distribuicao_labels.append('Investimentos')
            distribuicao_values.append(float(saldo_total_investimento))
        
        if saldo_total_cartoes_credito != 0:
            distribuicao_labels.append('Cartão de Crédito')
            distribuicao_values.append(float(saldo_total_cartoes_credito))
        
        # Dados para evolução do patrimônio (6 meses)
        evolucao_patrimonio = []
        if patrimonio_liquido != Decimal('0.00'):
            for i in range(6):
                mes_anterior = hoje - relativedelta(months=5 - i)
                valor_base = float(patrimonio_liquido)
                valor_simulado = valor_base * (0.8 + (i * 0.04))
                evolucao_patrimonio.append({
                    'mes': mes_anterior.strftime('%b/%y'),
                    'valor': round(valor_simulado, 2)
                })
        
        # Obter anos disponíveis para filtro
        anos_entradas = Entrada.objects.filter(
            conta_bancaria__proprietario=user
        ).dates('data', 'year')
        
        anos_saidas = Saida.objects.filter(
            conta_bancaria__proprietario=user
        ).dates('data_vencimento', 'year')
        
        anos_disponiveis = sorted(list(set(
            [d.year for d in anos_entradas] + 
            [d.year for d in anos_saidas] +
            [hoje.year, hoje.year - 1, hoje.year - 2]
        )), reverse=True)
        
        # Preparar contexto
        context = {
            'saldo_geral': saldo_geral,
            'saldo_disponivel': saldo_total_contas_ativas,
            'entradas_mes': entradas_mes_atual,
            'saidas_mes': saidas_mes_atual,
            'fluxo_mensal': fluxo_mensal,
            'patrimonio_liquido': patrimonio_liquido,
            'reserva_emergencia': reserva_emergencia,
            'meses_reserva': meses_reserva,
            'despesas_mensais_medias': despesas_mensais_medias,
            'receitas_mensais_medias': receitas_mensais_medias,
            'taxa_economia': taxa_economia,
            'total_dividas': total_dividas,
            'total_ativos': total_ativos,
            'contas': contas,
            'tipos_conta': ContaBancaria.TIPO_CONTA_CHOICES,
            'anos_disponiveis': anos_disponiveis,
            'evolucao_patrimonio': json.dumps(evolucao_patrimonio),
            'distribuicao_labels': json.dumps(distribuicao_labels),
            'distribuicao_values': json.dumps(distribuicao_values),
        }
        
        return render(request, 'core/saldo_atual.html', context)
        
    except Exception as e:
        print(f"Erro em saldo_atual: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Contexto de fallback em caso de erro
        context = {
            'saldo_geral': Decimal('0.00'),
            'saldo_disponivel': Decimal('0.00'),
            'entradas_mes': Decimal('0.00'),
            'saidas_mes': Decimal('0.00'),
            'fluxo_mensal': Decimal('0.00'),
            'patrimonio_liquido': Decimal('0.00'),
            'reserva_emergencia': Decimal('0.00'),
            'meses_reserva': Decimal('0.00'),
            'despesas_mensais_medias': Decimal('0.00'),
            'receitas_mensais_medias': Decimal('0.00'),
            'taxa_economia': Decimal('0.00'),
            'total_dividas': Decimal('0.00'),
            'total_ativos': Decimal('0.00'),
            'contas': ContaBancaria.objects.filter(proprietario=request.user),
            'tipos_conta': ContaBancaria.TIPO_CONTA_CHOICES,
            'anos_disponiveis': [date.today().year],
            'evolucao_patrimonio': json.dumps([]),
            'distribuicao_labels': json.dumps([]),
            'distribuicao_values': json.dumps([]),
        }
        
        return render(request, 'core/saldo_atual.html', context)

# ================================================================
# VIEWS DA PARTE DE TRANSFERÊNCIAS
# ================================================================


@login_required
def transferencia_list(request):
    meses_choices = [
        ('01', 'Janeiro'), ('02', 'Fevereiro'), ('03', 'Março'), ('04', 'Abril'),
        ('05', 'Maio'), ('06', 'Junho'), ('07', 'Julho'), ('08', 'Agosto'),
        ('09', 'Setembro'), ('10', 'Outubro'), ('11', 'Novembro'), ('12', 'Dezembro')
    ]
    
    hoje = dj_timezone.now()
    ano_atual = hoje.year
    mes_atual = hoje.month
    
    # Filtros
    ano_filter_str = request.GET.get('ano', str(ano_atual))
    mes_filter_str = request.GET.get('mes', str(mes_atual).zfill(2)) # Garante dois dígitos
    
    # Validar filtros
    try:
        ano_filter = int(ano_filter_str)
    except (ValueError, TypeError):
        ano_filter = ano_atual
    
    if mes_filter_str == '': # 'todos' os meses
        mes_num = None
    else:
        try:
            mes_num = int(mes_filter_str)
            if mes_num < 1 or mes_num > 12:
                mes_num = mes_atual
        except (ValueError, TypeError):
            mes_num = mes_atual
    
    # Busca transferências (Saídas marcadas como "Transferência Interna")
    transferencias_saidas_qs = Saida.objects.filter(
        usuario=request.user,
        local="Transferência Interna",
        data_lancamento__year=ano_filter
    )
    
    if mes_num:
        transferencias_saidas_qs = transferencias_saidas_qs.filter(data_lancamento__month=mes_num)
        mes_selecionado = str(mes_num).zfill(2)
    else:
        mes_selecionado = '' # Representa 'todos' os meses
    
    # Processar transferências para exibir no template
    transfers = []
    total_transferencias = Decimal('0.00')
    maior_transferencia = {'valor': Decimal('0.00')}
    
    for saida in transferencias_saidas_qs.order_by('-data_lancamento'):
        try:
            # Encontrar a entrada correspondente. Pode ser complicado se houver muitas transações no mesmo valor/data.
            # Uma forma mais robusta seria ter um campo de ligação entre Saida e Entrada para transferências.
            # Para este exemplo, vamos tentar encontrar uma entrada com o mesmo valor, na mesma data, para a conta destino da saída,
            # e que tenha sido criada como uma 'Transferência Interna'.
            entrada_correspondente = Entrada.objects.filter(
                usuario=request.user,
                valor=saida.valor,
                data=saida.data_lancamento,
                conta_bancaria__isnull=False, # Garante que a conta destino existe
                nome__icontains=f"Transferência de {saida.conta_bancaria.get_nome_banco_display()}" # Heurística para encontrar a entrada
            ).first() # Pega a primeira que encontrar
            
            if entrada_correspondente:
                transfer_data = {
                    'saida_obj': saida,
                    'entrada_obj': entrada_correspondente,
                    'conta_origem_display': saida.conta_bancaria.get_nome_banco_display(),
                    'conta_destino_display': entrada_correspondente.conta_bancaria.get_nome_banco_display(),
                    'valor': saida.valor
                }
                
                transfers.append(transfer_data)
                total_transferencias += saida.valor
                
                if saida.valor > maior_transferencia['valor']:
                    maior_transferencia = transfer_data
            
        except Exception as e:
            # Log de erro para depuração
            print(f"Erro ao processar transferência {saida.pk}: {e}")
            continue
    
    # Cálculos estatísticos
    media_transferencias = total_transferencias / len(transfers) if transfers else Decimal('0.00')
    
    # Saldos das contas
    saldos_contas = get_saldos_contas(request.user)
    
    # Contas para formulário do modal de transferência
    contas_para_form = ContaBancaria.objects.filter(
        proprietario=request.user,
        ativa=True,
        tipo__in=['corrente', 'poupanca']
    )
    
    # Anos disponíveis (busca anos com registros e adiciona alguns anos ao redor do atual)
    anos_com_registros = set(Saida.objects.filter(usuario=request.user, local="Transferência Interna").values_list('data_lancamento__year', flat=True))
    anos_disponiveis = sorted(list(anos_com_registros.union(range(ano_atual - 2, ano_atual + 2))), reverse=True)

    # Mapeamento de meses para badges
    meses_display_map = {k: v for k, v in meses_choices}
    
    form = TransferenciaForm(user=request.user) # Instancia o formulário para o modal
    
    context = {
        'transfers': transfers,
        'total_transferencias': total_transferencias,
        'maior_transferencia': maior_transferencia,
        'media_transferencias': media_transferencias,
        'saldos_contas': saldos_contas,
        'contas_para_form': contas_para_form, # Pode não ser necessário se o form for renderizado via AJAX
        'meses': meses_choices, # Para o select de filtro
        'anos_disponiveis': anos_disponiveis,
        'ano_selecionado': str(ano_filter), # Passa o ano filtrado (string)
        'mes_selecionado': mes_selecionado, # Passa o mês filtrado (string de 2 dígitos ou '')
        'mes_atual_nome': dict(meses_choices).get(str(mes_num).zfill(2), 'Todos os meses') if mes_num else 'Todos os meses',
        'ano_atual': ano_filter,
        'form': form, # Passa o formulário para o template
        'meses_display_map': meses_display_map, # Para os badges
    }
    
    return render(request, 'core/transferencia_list.html', context)
# views.py - Substitua as views de transferência por estas
@login_required
def transferencia_create(request):
    if request.method == 'POST':
        form = TransferenciaForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    conta_origem = form.cleaned_data['conta_origem']
                    conta_destino = form.cleaned_data['conta_destino']
                    valor_str = request.POST.get('valor_numerico', '0')
                    valor = Decimal(valor_str) if valor_str else Decimal('0')
                    descricao = form.cleaned_data.get('descricao', '')
                    
                    # Cria a saída (transferência da conta origem)
                    saida = Saida.objects.create(
                        usuario=request.user,
                        nome=f"Transferência para {conta_destino.get_nome_banco_display()}",
                        valor=valor,
                        data_lancamento=timezone.now().date(),
                        data_vencimento=timezone.now().date(),
                        local="Transferência Interna",
                        forma_pagamento="transferencia",
                        situacao="pago",
                        conta_bancaria=conta_origem,
                        observacao=descricao or f"Transferência para {conta_destino.get_nome_banco_display()}"
                    )
                    
                    # Cria a entrada (transferência para conta destino)
                    entrada = Entrada.objects.create(
                        usuario=request.user,
                        nome=f"Transferência de {conta_origem.get_nome_banco_display()}",
                        valor=valor,
                        data=timezone.now().date(),
                        forma_recebimento="transferencia",
                        conta_bancaria=conta_destino,
                        observacao=descricao or f"Transferência de {conta_origem.get_nome_banco_display()}"
                    )
                    
                    # Atualiza os saldos das contas
                    conta_origem.saldo_atual -= valor
                    conta_destino.saldo_atual += valor
                    conta_origem.save()
                    conta_destino.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Transferência realizada com sucesso!'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao realizar transferência: {str(e)}'
                })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data()
            })
    
    # GET request - retorna o formulário para o modal
    form = TransferenciaForm(user=request.user)
    
    # Renderiza o formulário para o modal
    form_html = render_to_string('core/includes/transferencia_form_modal.html', {
        'form': form
    }, request=request)
    
    return JsonResponse({
        'form_html': form_html
    })


@login_required
def transferencia_edit(request, pk):
    try:
        # Para edição, precisamos encontrar tanto a saída quanto a entrada
        saida = Saida.objects.get(pk=pk, usuario=request.user, local="Transferência Interna")
        
        # Encontra a entrada correspondente
        entrada = Entrada.objects.get(
            usuario=request.user,
            valor=saida.valor,
            data=saida.data_lancamento,
            observacao__icontains=saida.observacao
        )
        
        if request.method == 'POST':
            form = TransferenciaForm(request.POST, user=request.user)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        # Primeiro, reverte a transferência anterior
                        conta_origem_antiga = saida.conta_bancaria
                        conta_destino_antiga = entrada.conta_bancaria
                        valor_antigo = saida.valor
                        
                        conta_origem_antiga.saldo_atual += valor_antigo
                        conta_destino_antiga.saldo_atual -= valor_antigo
                        conta_origem_antiga.save()
                        conta_destino_antiga.save()
                        
                        # Agora processa a nova transferência
                        nova_conta_origem = form.cleaned_data['conta_origem']
                        nova_conta_destino = form.cleaned_data['conta_destino']
                        novo_valor = form.cleaned_data['valor']
                        nova_descricao = form.cleaned_data.get('descricao', '')
                        
                        # Atualiza a saída
                        saida.conta_bancaria = nova_conta_origem
                        saida.valor = novo_valor
                        saida.observacao = nova_descricao or f"Transferência para {nova_conta_destino.get_nome_banco_display()}"
                        saida.save()
                        
                        # Atualiza a entrada
                        entrada.conta_bancaria = nova_conta_destino
                        entrada.valor = novo_valor
                        entrada.observacao = nova_descricao or f"Transferência de {nova_conta_origem.get_nome_banco_display()}"
                        entrada.save()
                        
                        # Atualiza os saldos das novas contas
                        nova_conta_origem.saldo_atual -= novo_valor
                        nova_conta_destino.saldo_atual += novo_valor
                        nova_conta_origem.save()
                        nova_conta_destino.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Transferência atualizada com sucesso!'
                    })
                    
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'message': f'Erro ao atualizar transferência: {str(e)}'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.get_json_data()
                })
        
        # GET request - preenche o formulário com os dados atuais
        initial_data = {
            'conta_origem': saida.conta_bancaria.id,
            'conta_destino': entrada.conta_bancaria.id,
            'valor': saida.valor,
            'descricao': saida.observacao
        }
        
        form = TransferenciaForm(initial=initial_data, user=request.user)
        form_html = render_to_string('core/includes/transferencia_form_modal.html', {
            'form': form,
            'editing': True,
            'transferencia_id': pk
        }, request=request)
        
        return JsonResponse({
            'form_html': form_html
        })
        
    except (Saida.DoesNotExist, Entrada.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': 'Transferência não encontrada'
        })

@login_required
def transferencia_delete(request, pk):
    try:
        saida = Saida.objects.get(pk=pk, usuario=request.user, local="Transferência Interna")
        
        # Encontra a entrada correspondente
        entrada = Entrada.objects.get(
            usuario=request.user,
            valor=saida.valor,
            data=saida.data_lancamento,
            observacao__icontains=saida.observacao
        )
        
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    # Reverte a transferência
                    conta_origem = saida.conta_bancaria
                    conta_destino = entrada.conta_bancaria
                    valor = saida.valor
                    
                    conta_origem.saldo_atual += valor
                    conta_destino.saldo_atual -= valor
                    conta_origem.save()
                    conta_destino.save()
                    
                    # Exclui os registros
                    saida.delete()
                    entrada.delete()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Transferência excluída com sucesso!'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao excluir transferência: {str(e)}'
                })
        
        # Para GET, retorna informações para confirmação
        return JsonResponse({
            'success': True,
            'transfer_info': f"Transferência de R$ {saida.valor:.2f} de {saida.conta_bancaria.get_nome_banco_display()} para {entrada.conta_bancaria.get_nome_banco_display()}"
        })
        
    except (Saida.DoesNotExist, Entrada.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': 'Transferência não encontrada'
        })
    



# ================================================================
# VIEWS DA PROFILE (CORRIGIDAS)
# ================================================================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserUpdateForm, ProfileUpdateForm
from .models import Profile, UserActivity, UserLogin  # Importações corrigidas

import os
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@login_required
@transaction.atomic
def profile_update_view(request):
    # Obter ou criar o perfil do usuário
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        
        if u_form.is_valid() and p_form.is_valid():
            # Verificar se uma nova foto foi enviada
            if 'foto_perfil' in request.FILES:
                # Deletar a imagem antiga se existir
                if profile.foto_perfil and profile.foto_perfil.name != 'default.jpg':
                    try:
                        old_profile = Profile.objects.get(pk=profile.pk)
                        if (old_profile.foto_perfil and 
                            old_profile.foto_perfil.name != 'default.jpg' and 
                            old_profile.foto_perfil.name != profile.foto_perfil.name):
                            if os.path.isfile(old_profile.foto_perfil.path):
                                os.remove(old_profile.foto_perfil.path)
                    except Exception as e:
                        print(f"Erro ao deletar imagem antiga: {e}")
            
            u_form.save()
            p_form.save()
            
            # Processar tema se enviado via AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                theme = request.POST.get('theme')
                if theme in ['light', 'dark', 'auto']:
                    profile.theme = theme
                    profile.save()
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Preferências salvas com sucesso!'
                })
            
            messages.success(request, 'Seu perfil foi atualizado com sucesso!')
            return redirect('core:profile_update_view')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = {}
                if u_form.errors:
                    errors.update(u_form.errors.get_json_data())
                if p_form.errors:
                    errors.update(p_form.errors.get_json_data())
                return JsonResponse({
                    'success': False, 
                    'errors': errors
                }, status=400)
            
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)
    
    return render(request, 'core/profile_update.html', {
        'u_form': u_form,
        'p_form': p_form,
        'profile': profile  # Adicionar profile ao contexto
    })

@login_required
@require_POST
def password_change_view(request):
    """View para alteração de senha"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Atualizar a data da última alteração de senha
            request.user.profile.password_updated_at = timezone.now()
            request.user.profile.save()
            
            update_session_auth_hash(request, user)  # Manter o usuário logado
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': 'Senha alterada com sucesso!',
                    'password_updated_at': request.user.profile.password_updated_at.strftime('%d/%m/%Y %H:%M') if request.user.profile.password_updated_at else 'Nunca'
                })
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('core:profile_update_view')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors.get_json_data()}, status=400)
            messages.error(request, 'Erro ao alterar a senha.')
    return redirect('core:profile_update_view')


@login_required
def delete_account(request):
    if request.method == 'POST':
        confirm_text = request.POST.get('confirm_text', '')
        
        if confirm_text.upper() != 'EXCLUIR':
            messages.error(request, 'Confirmação incorreta. Digite "EXCLUIR" para confirmar.')
            return redirect('core:delete_account')
        
        try:
            user = request.user
            # Logout antes de deletar
            from django.contrib.auth import logout
            logout(request)
            user.delete()
            messages.success(request, 'Sua conta foi excluída com sucesso.')
            return redirect('core:home')
        except Exception as e:
            messages.error(request, f'Erro ao excluir conta: {str(e)}')
            return redirect('core:profile_update_view')
    
    return render(request, 'core/confirm_delete_account.html')


@login_required
@require_POST
def remove_profile_photo(request):
    """View para remover foto de perfil"""
    try:
        profile = request.user.profile
        if profile.foto_perfil and profile.foto_perfil.name != 'default.jpg':
            # Deleta o arquivo físico
            if os.path.isfile(profile.foto_perfil.path):
                os.remove(profile.foto_perfil.path)
            # Reseta para a imagem padrão
            profile.foto_perfil = 'default.jpg'
            profile.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Foto de perfil removida com sucesso.'})
            messages.success(request, 'Foto de perfil removida com sucesso.')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Você já está usando a foto padrão.'})
            messages.info(request, 'Você já está usando a foto padrão.')
            
    except Exception as e:
        error_msg = f'Erro ao remover foto: {str(e)}'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_msg})
        messages.error(request, error_msg)
    
    return redirect('core:profile_update_view')


@login_required
def track_login(request):
    """Registrar login do usuário"""
    try:
        user_profile = request.user.profile
        user_profile.update_login_streak()
        
        # Registrar login
        UserLogin.objects.create(
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Registrar atividade
        UserActivity.objects.create(
            user=request.user,
            activity_type='login',
            details={'ip': request.META.get('REMOTE_ADDR')}
        )
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
@require_POST
def update_profile_info(request):
    """View para atualizar informações do perfil"""
    user_form = UserUpdateForm(request.POST, instance=request.user)
    
    if user_form.is_valid():
        user_form.save()
        
        # Registrar atividade
        UserActivity.objects.create(
            user=request.user,
            activity_type='profile_update',
            details={'fields_updated': list(request.POST.keys())}
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Informações atualizadas com sucesso!',
            'profile_completion': request.user.profile.get_profile_completion()
        })
    
    return JsonResponse({'success': False, 'errors': user_form.errors.get_json_data()}, status=400)


@login_required
@require_POST
def update_profile_photo(request):
    """View para atualizar apenas a foto de perfil"""
    form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
    
    if form.is_valid():
        # Processar a imagem se fornecida
        if 'foto_perfil' in request.FILES:
            # Deletar a imagem antiga se existir
            if request.user.profile.foto_perfil and request.user.profile.foto_perfil.name != 'default.jpg':
                try:
                    if os.path.isfile(request.user.profile.foto_perfil.path):
                        os.remove(request.user.profile.foto_perfil.path)
                except Exception as e:
                    print(f"Erro ao deletar imagem antiga: {e}")
        
        form.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Foto de perfil atualizada com sucesso!'})
        messages.success(request, 'Foto de perfil atualizada com sucesso!')
    else:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors.get_json_data()}, status=400)
        messages.error(request, 'Erro ao atualizar a foto de perfil.')
    
    return redirect('core:profile_update_view')

from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@login_required
def user_statistics(request):
    """API para fornecer dados de estatísticas do usuário"""
    try:
        user = request.user
        profile = user.profile
        
        logger.info(f"Processando estatísticas para usuário: {user.username}")
        
        # Estatísticas básicas
        statistics = {
            'total_logins': profile.total_logins or 0,
            'login_streak': profile.login_streak or 0,
            'last_login': user.last_login.strftime('%d/%m/%Y %H:%M') if user.last_login else 'Nunca',
            'account_age_days': (timezone.now().date() - user.date_joined.date()).days,
            'profile_completion': profile.get_profile_completion(),
            'last_password_change': profile.password_updated_at.strftime('%d/%m/%Y %H:%M') if profile.password_updated_at else 'Nunca',
            'weekly_logins': 0,  # Será calculado abaixo
        }
        
        # Atividade semanal (últimos 7 dias)
        weekly_activity = []
        today = timezone.now().date()
        
        # Se o modelo UserLogin não existir, use dados simulados
        try:
            from .models import UserLogin
            for i in range(6, -1, -1):  # Últimos 7 dias
                date = today - timedelta(days=i)
                login_count = UserLogin.objects.filter(
                    user=user,
                    login_time__date=date
                ).count()
                weekly_activity.append({
                    'day': date.strftime('%d/%m'),
                    'count': login_count
                })
                statistics['weekly_logins'] += login_count
        except Exception as e:
            logger.warning(f"Modelo UserLogin não disponível, usando dados simulados: {e}")
            # Dados simulados para demonstração
            for i in range(6, -1, -1):
                date = today - timedelta(days=i)
                weekly_activity.append({
                    'day': date.strftime('%d/%m'),
                    'count': i + 1  # Dados de exemplo
                })
                statistics['weekly_logins'] += (i + 1)
        
        # Atividades recentes
        recent_activities = []
        try:
            from .models import UserActivity
            activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:5]
            for activity in activities:
                recent_activities.append({
                    'type': activity.activity_type,
                    'title': get_activity_display(activity.activity_type),
                    'description': get_activity_description(activity.activity_type),
                    'time': activity.timestamp.strftime('%d/%m/%Y %H:%M'),
                    'icon': get_activity_icon(activity.activity_type),
                    'color': get_activity_color(activity.activity_type)
                })
        except Exception as e:
            logger.warning(f"Modelo UserActivity não disponível: {e}")
            # Atividades de exemplo
            recent_activities = [
                {
                    'type': 'login',
                    'title': 'Login realizado',
                    'description': 'Acesso ao sistema',
                    'time': timezone.now().strftime('%d/%m/%Y %H:%M'),
                    'icon': 'fas fa-sign-in-alt',
                    'color': 'blue'
                }
            ]
        
        # Conquistas
        achievements = [
            {
                'title': 'Primeira Semana',
                'description': '7 dias consecutivos de acesso',
                'icon': 'fas fa-calendar-check',
                'icon_bg': 'bg-green-100',
                'icon_color': 'text-green-600',
                'achieved': (profile.login_streak or 0) >= 7,
                'progress': min(100, ((profile.login_streak or 0) / 7) * 100)
            },
            {
                'title': 'Perfil Completo',
                'description': '100% do perfil preenchido',
                'icon': 'fas fa-user-check',
                'icon_bg': 'bg-blue-100',
                'icon_color': 'text-blue-600',
                'achieved': profile.get_profile_completion() == 100,
                'progress': profile.get_profile_completion()
            },
            {
                'title': 'Segurança Máxima',
                'description': 'Senha forte configurada',
                'icon': 'fas fa-shield-alt',
                'icon_bg': 'bg-purple-100',
                'icon_color': 'text-purple-600',
                'achieved': profile.password_updated_at is not None,
                'progress': 100 if profile.password_updated_at else 0
            },
        ]
        
        logger.info(f"Estatísticas processadas com sucesso para {user.username}")
        
        return JsonResponse({
            'success': True,
            'statistics': statistics,
            'weekly_activity': weekly_activity,
            'recent_activities': recent_activities,
            'achievements': achievements
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar estatísticas: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Erro ao obter estatísticas: {str(e)}'
        })

# Funções auxiliares para atividades
def get_activity_display(activity_type):
    activity_names = {
        'login': 'Login realizado',
        'password_change': 'Senha alterada',
        'profile_update': 'Perfil atualizado',
        'photo_change': 'Foto alterada',
    }
    return activity_names.get(activity_type, 'Atividade do sistema')

def get_activity_description(activity_type):
    descriptions = {
        'login': 'Acesso ao sistema',
        'password_change': 'Alteração de segurança',
        'profile_update': 'Informações pessoais atualizadas',
        'photo_change': 'Foto de perfil modificada',
    }
    return descriptions.get(activity_type, 'Atividade do usuário')

def get_activity_icon(activity_type):
    icons = {
        'login': 'fas fa-sign-in-alt',
        'password_change': 'fas fa-key',
        'profile_update': 'fas fa-user-edit',
        'photo_change': 'fas fa-camera',
    }
    return icons.get(activity_type, 'fas fa-history')

def get_activity_color(activity_type):
    colors = {
        'login': 'blue',
        'password_change': 'green',
        'profile_update': 'purple',
        'photo_change': 'yellow',
    }
    return colors.get(activity_type, 'gray')
    """API para fornecer dados de estatísticas do usuário"""
    try:
        user = request.user
        profile = user.profile
        
        # Estatísticas básicas
        statistics = {
            'total_logins': profile.total_logins,
            'login_streak': profile.login_streak,
            'last_login': user.last_login.strftime('%d/%m/%Y %H:%M') if user.last_login else 'Nunca',
            'account_age_days': (timezone.now().date() - user.date_joined.date()).days,
            'profile_completion': profile.get_profile_completion(),
            'last_password_change': profile.password_updated_at.strftime('%d/%m/%Y %H:%M') if profile.password_updated_at else 'Nunca',
        }
        
        # Atividade semanal (últimos 7 dias)
        weekly_activity = []
        today = timezone.now().date()
        for i in range(6, -1, -1):  # Últimos 7 dias
            date = today - timedelta(days=i)
            login_count = UserLogin.objects.filter(
                user=user,
                login_time__date=date
            ).count()
            weekly_activity.append({
                'day': date.strftime('%d/%m'),
                'count': login_count
            })
        
        # Atividades recentes (últimas 5 atividades)
        recent_activities = []
        activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:5]
        for activity in activities:
            # Determinar ícone e cores baseados no tipo de atividade
            icon_config = {
                'login': {'icon': 'fas fa-sign-in-alt', 'color': 'blue'},
                'password_change': {'icon': 'fas fa-key', 'color': 'green'},
                'profile_update': {'icon': 'fas fa-user-edit', 'color': 'purple'},
                'photo_change': {'icon': 'fas fa-camera', 'color': 'yellow'},
            }
            
            config = icon_config.get(activity.activity_type, {'icon': 'fas fa-history', 'color': 'gray'})
            
            recent_activities.append({
                'type': activity.activity_type,
                'title': activity.get_activity_display(),
                'description': activity.get_description(),
                'time': activity.timestamp.strftime('%d/%m/%Y %H:%M'),
                'icon': config['icon'],
                'color': config['color']
            })
        
        # Conquistas
        achievements = [
            {
                'title': 'Primeira Semana',
                'description': '7 dias consecutivos de acesso',
                'icon': 'fas fa-calendar-check',
                'icon_bg': 'bg-green-100',
                'icon_color': 'text-green-600',
                'achieved': profile.login_streak >= 7,
                'progress': min(100, (profile.login_streak / 7) * 100)
            },
            {
                'title': 'Perfil Completo',
                'description': '100% do perfil preenchido',
                'icon': 'fas fa-user-check',
                'icon_bg': 'bg-blue-100',
                'icon_color': 'text-blue-600',
                'achieved': profile.get_profile_completion() == 100,
                'progress': profile.get_profile_completion()
            },
            {
                'title': 'Segurança Máxima',
                'description': 'Senha forte configurada',
                'icon': 'fas fa-shield-alt',
                'icon_bg': 'bg-purple-100',
                'icon_color': 'text-purple-600',
                'achieved': profile.password_updated_at is not None,
                'progress': 100 if profile.password_updated_at else 0
            },
        ]
        
        return JsonResponse({
            'success': True,
            'statistics': statistics,
            'weekly_activity': weekly_activity,
            'recent_activities': recent_activities,
            'achievements': achievements
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao obter estatísticas: {str(e)}'
        })