"""Adaptador de correo transaccional.

En el MVP se limita a registrar el mensaje en el log. La firma esta pensada
para sustituirse mas adelante por SMTP / Resend / SES sin tocar los llamadores.
"""

import logging

logger = logging.getLogger("sportyclub.email")


def send_email(to: str, subject: str, body: str) -> None:
    logger.info(
        "EMAIL -> %s | %s\n%s",
        to,
        subject,
        body,
    )


def send_invitation_email(
    to: str,
    club_name: str,
    invite_url: str,
) -> None:
    send_email(
        to=to,
        subject=f"Invitacion para unirte a {club_name}",
        body=(
            f"Has sido invitado a {club_name} en SportyClub.\n"
            f"Acepta la invitacion aqui: {invite_url}\n"
            "Si no esperabas este correo, puedes ignorarlo."
        ),
    )


def send_password_reset_email(to: str, reset_url: str) -> None:
    send_email(
        to=to,
        subject="Restablece tu contrasena de SportyClub",
        body=(
            "Solicitaste restablecer tu contrasena.\n"
            f"Usa este enlace: {reset_url}\n"
            "Si no lo solicitaste, puedes ignorar este correo."
        ),
    )
