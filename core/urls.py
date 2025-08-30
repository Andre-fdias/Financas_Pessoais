from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    # Páginas principais
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    # Reset de senha
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='core/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='core/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'), name='password_reset_complete'),
    path('profile/change-password/', views.password_change_view, name='password_change_view'),


    # Perfil do usuário (URLs simplificadas)
    path('profile/', views.profile_update_view, name='profile'),  # Página principal do perfil
    path('profile/update/', views.profile_update_view, name='profile_update'),
    path('profile/change-password/', views.password_change_view, name='password_change'),
    path('profile/delete-account/', views.delete_account, name='delete_account'),
    path('profile/remove-photo/', views.remove_profile_photo, name='remove_profile_photo'),
    
    # APIs para perfil (AJAX)
    path('api/profile/update-info/', views.update_profile_info, name='update_profile_info'),
    path('api/profile/update-photo/', views.update_profile_photo, name='update_profile_photo'),
    path('api/profile/statistics/', views.user_statistics, name='user_statistics'),
    path('api/profile/track-login/', views.track_login, name='track_login'),

    # Contas Bancárias
    path('contas/', views.conta_list, name='conta_list'),
    path('contas/nova/', views.conta_create, name='conta_create'),
    path('contas/nova_modal/', views.conta_create_modal, name='conta_create_modal'),
    path('contas/<int:pk>/editar/', views.conta_update, name='conta_update'),
    path('contas/<int:pk>/excluir/', views.conta_delete, name='conta_delete'),
    path('get_banco_code/', views.get_banco_code, name='get_banco_code'),

    # Entradas (Receitas)
    path('entradas/', views.entrada_list, name='entrada_list'),
    path('entradas/nova/', views.entrada_create, name='entrada_create'),
    path('entradas/<int:pk>/editar/', views.entrada_update, name='entrada_update'),
    path('entradas/<int:pk>/excluir/', views.entrada_delete, name='entrada_delete'),

    # Saídas (Despesas)
    path('saidas/', views.saida_list, name='saida_list'),
    path('saidas/nova/', views.saida_create, name='saida_create'),
    path('saidas/<int:saida_id>/marcar-pago/', views.MarcarComoPagoView.as_view(), name='marcar_como_pago'),
    path('saidas/<int:pk>/editar/', views.saida_update, name='saida_update'),
    path('saidas/<int:pk>/excluir/', views.saida_delete, name='saida_delete'),
    path('saidas/choices/', views.get_saida_choices, name='saida_choices'),


    # Relatórios e Extratos
    path('extrato/', views.extrato_completo, name='extrato_completo'),
    path('saldo/', views.saldo_atual, name='saldo_atual'),

    # APIs para transações
    path('api/transacao/<int:pk>/detalhes/', views.transacao_detalhes, name='transacao_detalhes'),
    path('api/transacao/<int:pk>/marcar-pago/', views.marcar_como_pago, name='marcar_como_pago'),

    # Transferências
    path('transferencias/', views.transferencia_list, name='transferencia_list'),
    path('transferencias/nova/', views.transferencia_create, name='transferencia_create'),
    path('transferencias/<int:pk>/editar/', views.transferencia_edit, name='transferencia_edit'),
    path('transferencias/<int:pk>/excluir/', views.transferencia_delete, name='transferencia_delete'),
    path('get-account-balance/<int:pk>/', views.get_account_balance, name='get_account_balance'),
]