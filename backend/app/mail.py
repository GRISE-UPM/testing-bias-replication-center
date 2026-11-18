"""Outgoing email.

Real delivery will use Amazon SES. Until then messages are only logged and kept
in memory, so that behaviour can be developed and tested without sending anything.
"""
import logging
from dataclasses import dataclass

log = logging.getLogger("mail")


@dataclass(frozen=True)
class Message:
    to: str
    subject: str
    body: str


outbox: list[Message] = []


def send_email(to: str, subject: str, body: str) -> None:
    outbox.append(Message(to, subject, body))
    log.info("EMAIL (not sent, development stub) to=%s subject=%s", to, subject)
