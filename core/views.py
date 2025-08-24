from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomUserCreationForm

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
    mes_filtro = request.GET.get('mes', str(mes_atual).zfill(2))  # Garantir 2 dígitos
    forma_filtro = request.GET.get('forma')
    
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
    
    if forma_filtro:
        entradas = entradas.filter(forma_recebimento=forma_filtro)
    
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
        mes_nome = dict(meses).get(mes_num, '')
    else:
        mes_nome = f'Todos os meses de {ano_filtro}'
    
    # Obter contas bancárias para o modal
    contas_bancarias = ContaBancaria.objects.filter(proprietario=request.user, ativa=True)
    
    # Gerar lista de anos (2 anos atrás, atual, 1 ano à frente)
    anos_disponiveis = list(range(ano_atual - 2, ano_atual + 2))
    
    return render(request, 'core/entrada_list.html', {
        'entradas': entradas.order_by('-data'),
        'meses': meses,
        'anos_disponiveis': anos_disponiveis,
        'ano_selecionado': ano_filtro,
        'mes_selecionado': mes_selecionado,
        'forma_filtro': forma_filtro,
        'total_entradas': total_filtrado,
        'entradas_mes_atual': total_filtrado,
        'media_mensal': media_mensal,
        'variacao_mensal': variacao_mensal,
        'mes_atual_nome': mes_nome,
        'ano_atual': ano_filtro,  # Usar o ano filtrado, não necessariamente o atual
        'FORMA_RECEBIMENTO_CHOICES': FORMA_RECEBIMENTO_CHOICES,
        'contas_bancarias': contas_bancarias,
        'mes_atual_num': str(mes_atual).zfill(2)  # Para uso no template
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
    
    # Obter contas bancárias e categorias para os modais
    contas_bancarias = ContaBancaria.objects.filter(proprietario=request.user, ativa=True)

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
        'CATEGORIA_CHOICES': CATEGORIA_CHOICES,
        'SUBCATEGORIA_CHOICES': SUBCATEGORIA_CHOICES,
        'FORMA_PAGAMENTO_CHOICES': FORMA_PAGAMENTO_CHOICES,
        'TIPO_PAGAMENTO_DETALHE_CHOICES': TIPO_PAGAMENTO_DETALHE_CHOICES,
        'SITUACAO_CHOICES': SITUACAO_CHOICES,
        'PERIODICIDADE_CHOICES': PERIODICIDADE_CHOICES,  # Adicionado
        'contas_bancarias': contas_bancarias
    })

@login_required
def saida_create(request):
    if request.method == 'POST':
        form = SaidaForm(request.POST, user=request.user)
        if form.is_valid():
            saida = form.save(commit=False)
            saida.usuario = request.user
            saida.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Despesa cadastrada com sucesso!'})
            else:
                messages.success(request, 'Despesa cadastrada com sucesso!')
                return redirect('core:saida_list')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Retorna os erros de validação diretamente
                errors = {field: [str(error) for error in error_list] for field, error_list in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors}, status=400)

    else: # GET request (quando o botão "Adicionar" é clicado)
        form = SaidaForm(user=request.user)
        # Obter contas bancárias do usuário (passado para o template principal)
        contas_bancarias = ContaBancaria.objects.filter(proprietario=request.user, ativa=True)

        # Se for requisição AJAX (para abrir o modal), não precisamos renderizar HTML
        # O JS do modal já tem o HTML e vai preencher os campos.
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True}) # Apenas um OK para o JS

    # Se for requisição normal (não AJAX), renderizar a página completa
    return render(request, 'core/saida_form.html', {
        'form': form,
        'action': 'Criar',
        'FORMA_PAGAMENTO_CHOICES': FORMA_PAGAMENTO_CHOICES,
        'SITUACAO_CHOICES': SITUACAO_CHOICES,
        'CATEGORIA_CHOICES': CATEGORIA_CHOICES,
        'SUBCATEGORIA_CHOICES': SUBCATEGORIA_CHOICES,
        'TIPO_PAGAMENTO_DETALHE_CHOICES': TIPO_PAGAMENTO_DETALHE_CHOICES,
        'PERIODICIDADE_CHOICES': PERIODICIDADE_CHOICES,
        'contas_bancarias': contas_bancarias # Ainda passa para o template completo
    })

@login_required
def saida_update(request, pk):
    saida = get_object_or_404(Saida, pk=pk, usuario=request.user)

    if request.method == 'POST':
        form = SaidaForm(request.POST, instance=saida, user=request.user)
        if form.is_valid():
            form.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Despesa atualizada com sucesso!'})
            else:
                messages.success(request, 'Despesa atualizada com sucesso!')
                return redirect('core:saida_list')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Retorna os erros de validação diretamente
                errors = {field: [str(error) for error in error_list] for field, error_list in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors}, status=400)

    else: # GET request (quando o botão "Editar" é clicado)
        form = SaidaForm(instance=saida, user=request.user)

    # Obter contas bancárias do usuário (para o template normal e para os dados do modal GET)
    contas_bancarias = ContaBancaria.objects.filter(proprietario=request.user, ativa=True)

    # Se for requisição AJAX (para abrir o modal para edição), retornar JSON com os dados para preenchimento
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'id': saida.pk,
            'nome': saida.nome,
            'valor': str(saida.valor),
            'data_lancamento': saida.data_lancamento.isoformat() if saida.data_lancamento else '',
            'data_vencimento': saida.data_vencimento.isoformat() if saida.data_vencimento else '',
            'local': saida.local if saida.local else '',
            'categoria': saida.categoria if saida.categoria else '',
            'subcategoria': saida.subcategoria if saida.subcategoria else '',
            'forma_pagamento': saida.forma_pagamento if saida.forma_pagamento else '',
            'tipo_pagamento_detalhe': saida.tipo_pagamento_detalhe if saida.tipo_pagamento_detalhe else '',
            'situacao': saida.situacao if saida.situacao else '',
            'quantidade_parcelas': saida.quantidade_parcelas if saida.quantidade_parcelas else 1,
            'recorrente': saida.recorrente if saida.recorrente else '',
            'observacao': saida.observacao if saida.observacao else '',
            'conta_bancaria': saida.conta_bancaria.pk if saida.conta_bancaria else '', # Retorna o PK da conta
            'valor_parcela': str(saida.valor_parcela) if saida.valor_parcela else ''
        })

    # Se for requisição normal (não AJAX), renderizar a página completa
    return render(request, 'core/saida_form.html', {
        'form': form,
        'action': 'Editar',
        'FORMA_PAGAMENTO_CHOICES': FORMA_PAGAMENTO_CHOICES,
        'SITUACAO_CHOICES': SITUACAO_CHOICES,
        'CATEGORIA_CHOICES': CATEGORIA_CHOICES,
        'SUBCATEGORIA_CHOICES': SUBCATEGORIA_CHOICES,
        'TIPO_PAGAMENTO_DETALHE_CHOICES': TIPO_PAGAMENTO_DETALHE_CHOICES,
        'PERIODICIDADE_CHOICES': PERIODICIDADE_CHOICES,
        'contas_bancarias': contas_bancarias
    })

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
    user = request.user # Define o user uma vez
    try:
        contas = ContaBancaria.objects.filter(proprietario=user) # Use 'user'

        saldo_por_conta = {}
        saldo_geral = Decimal('0.00')

        tipo_filtro = request.GET.get('tipo', 'todos')
        status_filtro = request.GET.get('status', 'todas')

        contas_filtradas = contas
        if tipo_filtro != 'todos':
            contas_filtradas = contas_filtradas.filter(tipo=tipo_filtro)
        if status_filtro == 'ativas':
            contas_filtradas = contas_filtradas.filter(ativa=True)
        elif status_filtro == 'inativas':
            contas_filtradas = contas_filtradas.filter(ativa=False)

        saldo_total_contas_ativas = Decimal('0.00')
        saldo_total_cartoes_credito = Decimal('0.00')
        saldo_total_contas_corrente = Decimal('0.00')
        saldo_total_contas_poupanca = Decimal('0.00')
        
        limite_total_cartoes = Decimal('0.00')
        gastos_total_cartoes = Decimal('0.00')

        for conta in contas_filtradas:
            # Corrigido: Passe 'user' para get_sum em vez de request.user
            entradas_conta = get_sum(Entrada.objects.filter(usuario=user, conta_bancaria=conta))
            # Corrigido: Passe 'user' para get_sum em vez de request.user
            saidas_conta = get_sum(Saida.objects.filter(usuario=user, conta_bancaria=conta))

            if conta.tipo == 'credito':
                saldo_individual = saidas_conta
                
                if conta.limite_cartao:
                    limite_total_cartoes += conta.limite_cartao
                    gastos_total_cartoes += saidas_conta
            else:
                saldo_individual = (conta.saldo_atual or Decimal('0.00')) + entradas_conta - saidas_conta

            if conta.tipo in ['corrente', 'poupanca']:
                conta_nome = f"{conta.get_nome_banco_display()} - {conta.agencia or ''}/{conta.numero_conta or ''}"
            else:
                conta_nome = f"{conta.get_nome_banco_display()} - {conta.numero_conta or 'Cartão'}"

            saldo_por_conta[conta_nome] = saldo_individual
            saldo_geral += saldo_individual

            if conta.ativa:
                if conta.tipo == 'credito':
                    saldo_total_cartoes_credito += saldo_individual
                elif conta.tipo == 'corrente':
                    saldo_total_contas_corrente += saldo_individual
                elif conta.tipo == 'poupanca':
                    saldo_total_contas_poupanca += saldo_individual

                saldo_total_contas_ativas += saldo_individual

        limite_cartao_credito_disponivel = limite_total_cartoes - gastos_total_cartoes
        
        historico_labels, historico_data = get_saldo_historico(user, meses=12) # Use 'user'

        ultimas_transacoes = get_transacoes_recentes(user, limite=5) # Use 'user'

        saldo_por_tipo_data = get_saldo_por_tipo_conta(user) # Use 'user'
        saldo_tipos_labels = list(saldo_por_tipo_data.keys())
        saldo_tipos_values = list(saldo_por_tipo_data.values())

        entradas_forma_recebimento_data = get_entradas_por_forma_recebimento(user) # Use 'user'

        today = date.today()
        mes_anterior_date = today - relativedelta(months=1)

        # Corrigido: Passe 'user'
        entradas_mes_atual = get_sum(Entrada.objects.filter(usuario=user, data__year=today.year, data__month=today.month))
        # Corrigido: Passe 'user'
        saidas_mes_atual = get_sum(Saida.objects.filter(usuario=user, data_vencimento__year=today.year, data_vencimento__month=today.month))
        saldo_mes_atual = entradas_mes_atual - saidas_mes_atual

        # Corrigido: Passe 'user'
        entradas_mes_anterior = get_sum(Entrada.objects.filter(usuario=user, data__year=mes_anterior_date.year, data__month=mes_anterior_date.month))
        # Corrigido: Passe 'user'
        saidas_mes_anterior = get_sum(Saida.objects.filter(usuario=user, data_vencimento__year=mes_anterior_date.year, data_vencimento__month=mes_anterior_date.month))
        saldo_mes_anterior = entradas_mes_anterior - saidas_mes_anterior

        variacao_saldo_mensal = Decimal('0.00')
        if saldo_mes_anterior != Decimal('0.00'):
            variacao_saldo_mensal = ((saldo_mes_atual - saldo_mes_anterior) / abs(saldo_mes_anterior) * 100).quantize(Decimal('0.01'))
        elif saldo_mes_atual > Decimal('0.00'):
            variacao_saldo_mensal = Decimal('100.00')
        elif saldo_mes_atual < Decimal('0.00'):
            variacao_saldo_mensal = Decimal('-100.00')

        context = {
            'saldo_geral': saldo_geral,
            'saldo_por_conta': saldo_por_conta,
            'historico_labels': json.dumps(historico_labels),
            'historico_data': json.dumps(historico_data),
            'ultimas_transacoes': ultimas_transacoes,
            'saldo_tipos_labels': json.dumps(saldo_tipos_labels),
            'saldo_tipos_values': json.dumps(saldo_tipos_values),
            'variacao_saldo_mensal': variacao_saldo_mensal,
            'mes_comparacao': mes_anterior_date.strftime('%b/%Y'),

            'saldo_disponivel': saldo_total_contas_ativas,
            'limite_cartao_credito_disponivel': limite_cartao_credito_disponivel,
            'saldo_conta_corrente': saldo_total_contas_corrente,
            'saldo_poupanca': saldo_total_contas_poupanca,

            'tipos_conta_choices': ContaBancaria.TIPO_CONTA_CHOICES,
            'tipo_filtro_selecionado': tipo_filtro,
            'status_filtro_selecionado': status_filtro,

            'entradas_forma_recebimento_labels': json.dumps(entradas_forma_recebimento_data['labels']),
            'entradas_forma_recebimento_values': json.dumps(entradas_forma_recebimento_data['data']),
        }

        return render(request, 'core/saldo_atual.html', context)

    except Exception as e:
        print(f"Erro em saldo_atual: {str(e)}")
        import traceback
        traceback.print_exc()

        messages.error(request, f"Erro ao carregar saldo: {str(e)}")
        return render(request, 'core/saldo_atual.html', {
            'saldo_geral': Decimal('0.00'),
            'saldo_por_conta': {},
            'historico_labels': json.dumps([]),
            'historico_data': json.dumps([]),
            'ultimas_transacoes': [],
            'saldo_tipos_labels': json.dumps([]),
            'saldo_tipos_values': json.dumps([]),
            'variacao_saldo_mensal': Decimal('0.00'),
            'mes_comparacao': '',
            'saldo_disponivel': Decimal('0.00'),
            'limite_cartao_credito_disponivel': Decimal('0.00'),
            'saldo_conta_corrente': Decimal('0.00'),
            'saldo_poupanca': Decimal('0.00'),
            'tipos_conta_choices': ContaBancaria.TIPO_CONTA_CHOICES,
            'tipo_filtro_selecionado': 'todos',
            'status_filtro_selecionado': 'todas',
            'entradas_forma_recebimento_labels': json.dumps([]),
            'entradas_forma_recebimento_values': json.dumps([]),
        })


# ================================================================
# VIEWS DA PARTE DE TRANSFERÊNCIAS
# ================================================================


@login_required
def transferencia_list(request):
    meses_choices = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]
    
    hoje = dj_timezone.now()
    ano_atual = hoje.year
    mes_atual = hoje.month
    
    # Filtros
    ano_filtro = request.GET.get('ano', str(ano_atual))
    mes_filtro = request.GET.get('mes', str(mes_atual).zfill(2))
    
    # Validar filtros
    try:
        ano_filtro = int(ano_filtro)
    except (ValueError, TypeError):
        ano_filtro = ano_atual
    
    if mes_filtro == 'todos':
        mes_num = None
    else:
        try:
            mes_num = int(mes_filtro)
            if mes_num < 1 or mes_num > 12:
                mes_num = mes_atual
        except (ValueError, TypeError):
            mes_num = mes_atual
    
    # Busca transferências
    transferencias_saidas = Saida.objects.filter(
        usuario=request.user,
        local="Transferência Interna",
        data_lancamento__year=ano_filtro
    )
    
    if mes_num:
        transferencias_saidas = transferencias_saidas.filter(data_lancamento__month=mes_num)
        mes_selecionado = str(mes_num).zfill(2)
    else:
        mes_selecionado = 'todos'
    
    # Processar transferências
    transfers = []
    total_transferencias = Decimal('0.00')
    maior_transferencia = {'valor': Decimal('0.00')}
    
    for saida in transferencias_saidas:
        try:
            entrada_correspondente = Entrada.objects.get(
                usuario=request.user,
                valor=saida.valor,
                data=saida.data_lancamento,
                local="Transferência Interna",
                nome__icontains="Transferência recebida"
            )
            
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
            
        except (Entrada.DoesNotExist, Entrada.MultipleObjectsReturned):
            continue
    
    # Cálculos estatísticos
    media_transferencias = total_transferencias / len(transfers) if transfers else Decimal('0.00')
    
    # Saldos das contas
    saldos_contas = get_saldos_contas(request.user)
    
    # Contas para formulário
    contas_para_form = ContaBancaria.objects.filter(
        proprietario=request.user,
        ativa=True,
        tipo__in=['corrente', 'poupanca']
    )
    
    # Anos disponíveis
    anos_disponiveis = list(range(ano_atual - 2, ano_atual + 2))
    
    context = {
        'transfers': transfers,
        'total_transferencias': total_transferencias,
        'maior_transferencia': maior_transferencia,
        'media_transferencias': media_transferencias,
        'saldos_contas': saldos_contas,
        'contas_para_form': contas_para_form,
        'meses': meses_choices,
        'anos_disponiveis': anos_disponiveis,
        'ano_selecionado': ano_filtro,
        'mes_selecionado': mes_selecionado,
        'mes_atual_nome': dict(meses_choices).get(mes_num, 'Todos os meses') if mes_num else 'Todos os meses',
        'ano_atual': ano_atual,
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