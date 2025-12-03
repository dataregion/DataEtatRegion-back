from .configuration import (
    mail_enabled,
    mail_host,
    mail_from,
    mail_login,
    mail_password,
    mail_port,
    mail_to,
)
from dataclasses import dataclass
import smtplib
from email.message import EmailMessage


@dataclass
class SendMailCtx:
    success: bool


class SendEmail:
    def __init__(self, ctx: SendMailCtx) -> None:
        self.ctx = ctx

    def subject(self):
        return "✅ Load tests réussis" if self.ctx.success else "❌ Load tests échoués"

    def content(self):
        return (
            "Les tests de charge se sont terminés avec succès."
            if self.ctx.success
            else "Les tests de charge ont échoué. Veuillez vérifier les logs."
        )

    def send(self):
        if not mail_enabled():
            print("Mail sending is disabled.")
            return
        msg = EmailMessage()
        msg["Subject"] = self.subject()
        msg["From"] = mail_from()
        msg["To"] = mail_to()
        msg.set_content(self.content())

        with smtplib.SMTP_SSL(mail_host(), mail_port()) as smtp:  # ou votre serveur SMTP/port
            smtp.login(mail_login(), mail_password())  # utilisez un mot de passe d'application
            smtp.send_message(msg)
        print("Email sent successfully.")
