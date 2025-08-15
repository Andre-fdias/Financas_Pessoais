from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import re
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


class CustomUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('O e-mail é um campo obrigatório'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser deve ter is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser deve ter is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)

# Validador de CPF
cpf_validator = RegexValidator(
    regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
    message='CPF deve estar no formato: 000.000.000-00'
)

def validate_cpf(value):
    cpf_numeros = re.sub(r'[^0-9]', '', value)
    
    if len(cpf_numeros) != 11:
        raise ValidationError("CPF deve conter 11 dígitos.")
    
    if len(set(cpf_numeros)) == 1:
        raise ValidationError("CPF inválido.")

    # Implementar a validação completa do CPF se necessário.
    
class CustomUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(_('first name'), max_length=30, blank=False)
    last_name = models.CharField(_('last name'), max_length=30, blank=False)
    email = models.EmailField(_('email address'), unique=True)
    cpf = models.CharField(
        _('cpf'),
        max_length=14,
        unique=True,
        validators=[cpf_validator, validate_cpf]
    )
    data_nascimento = models.DateField(_('data de nascimento'), blank=False, null=False)
    must_change_password = models.BooleanField(default=False)
    
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'cpf', 'data_nascimento']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_short_name(self):
        return self.first_name