# accounts/utils.py
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)

def send_welcome_email(user, password):
    """
    Envia e-mail de boas-vindas com a senha temporária.
    """
    try:
        subject = 'Bem-vindo ao Sistema de Finanças Pessoais'
        html_message = render_to_string('accounts/email/welcome.html', {
            'user': user,
            'password': password,
        })
        plain_message = strip_tags(html_message)

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"E-mail de boas-vindas enviado com sucesso para {user.email}")
        return True
    except Exception as e:
        # Em produção, usar logging
        logger.error(f"Erro ao enviar e-mail para {user.email}: {e}", exc_info=True)
        return False