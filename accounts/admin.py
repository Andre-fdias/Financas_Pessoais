from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'cpf', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'must_change_password')
    search_fields = ('email', 'first_name', 'last_name', 'cpf')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'cpf', 'data_nascimento')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
        ('Segurança', {'fields': ('must_change_password',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)