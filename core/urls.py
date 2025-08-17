from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:login'), name='logout'),
    path('register/', views.register, name='register'),


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
    path('get-subcategorias/', views.GetSubcategoriasView.as_view(), name='get_subcategorias'),
  
  
    # URLs para Extrato & Saldo
    path('extrato/', views.extrato_completo, name='extrato_completo'),
    path('saldo/', views.saldo_atual, name='saldo_atual'),

    # URLs para Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
]
