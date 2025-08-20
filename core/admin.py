from django.contrib import admin
from .models import ContaBancaria, Entrada, Saida

# Register your models here.


@admin.register(ContaBancaria)
class ContaBancariaAdmin(admin.ModelAdmin):
    list_display = ('nome_banco', 'agencia', 'numero_conta', 'tipo', 'proprietario', 'ativa')
    list_filter = ('tipo', 'ativa', 'nome_banco')
    search_fields = ('nome_banco', 'agencia', 'numero_conta', 'proprietario__username')


admin.site.register(Entrada)
admin.site.register(Saida)
