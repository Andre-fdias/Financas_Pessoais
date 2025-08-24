from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:login'), name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'), # Adicionado

    # URLs para Reset de senha
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='core/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='core/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'), name='password_reset_complete'),

    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='core/password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='core/password_change_done.html'), name='password_change_done'),


    # URLs para Conta Bancária
    path('contas/', views.conta_list, name='conta_list'),
    path('contas/nova/', views.conta_create, name='conta_create'),
    path('contas/nova_modal/', views.conta_create_modal, name='conta_create_modal'), # Nova URL para o modal
    path('contas/<int:pk>/editar/', views.conta_update, name='conta_update'),
    path('contas/<int:pk>/excluir/', views.conta_delete, name='conta_delete'),
#
    path('get_banco_code/', views.get_banco_code, name='get_banco_code'),
    # URLs para Entrada (Receitas)
    path('entradas/', views.entrada_list, name='entrada_list'),
    path('entradas/nova/', views.entrada_create, name='entrada_create'),
    path('entradas/<int:pk>/editar/', views.entrada_update, name='entrada_update'),
    path('entradas/<int:pk>/excluir/', views.entrada_delete, name='entrada_delete'),

    # URLs para Saída (Despesas)
    path('saidas/', views.saida_list, name='saida_list'),
    path('saidas/nova/', views.saida_create, name='saida_create'),
    path('saidas/<int:pk>/editar/', views.saida_update, name='saida_update'),
    path('saidas/<int:pk>/excluir/', views.saida_delete, name='saida_delete'),
   # path('get-subcategorias/', views.get_subcategorias, name='get_subcategorias'), # Adicionado
    path('extrato/', views.extrato_completo, name='extrato_completo'), # Adicionado
    path('saldo/', views.saldo_atual, name='saldo_atual'), # Adicionado
# urls.py
    path('api/transacao/<int:pk>/detalhes/', views.transacao_detalhes, name='transacao_detalhes'),
    path('api/transacao/<int:pk>/marcar-pago/', views.marcar_como_pago, name='marcar_como_pago'),
    # URLs para Categorias e Subcategorias (se existirem)
    # path('categorias/', views.categoria_list, name='categoria_list'),
    # path('categorias/nova/', views.categoria_create, name='categoria_create'),
    # path('categorias/<int:pk>/editar/', views.categoria_update, name='categoria_update'),
    # path('categorias/<int:pk>/excluir/', views.categoria_delete, name='categoria_delete'),

    # path('subcategorias/', views.subcategoria_list, name='subcategoria_list'),
    # path('subcategorias/nova/', views.subcategoria_create, name='subcategoria_create'),
    # path('subcategorias/<int:pk>/editar/', views.subcategoria_update, name='subcategoria_update'),
    # path('subcategorias/<int:pk>/excluir/', views.subcategoria_delete, name='subcategoria_delete'),


    
    
    # URLs para Transferências (CRUD completo)
    path('transferencias/', views.transferencia_list, name='transferencia_list'),
    path('transferencias/nova/', views.transferencia_create, name='transferencia_create'),
    path('transferencias/<int:pk>/editar/', views.transferencia_edit, name='transferencia_edit'),
    path('transferencias/<int:pk>/excluir/', views.transferencia_delete, name='transferencia_delete'),
    path('get-account-balance/<int:pk>/', views.get_account_balance, name='get_account_balance'),
]
