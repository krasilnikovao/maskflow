import logging
import sys
from typing import Any

import structlog

# FIX 2.2: расширенный список чувствительных ключей
SENSITIVE_KEYS = {
    # Сырые значения
    "value",
    "text",
    "content",
    "source_text",
    "raw",
    # Контактные данные
    "email",
    "phone",
    # ФИО и персональные данные
    "fio",
    "name",
    "surname",
    "firstname",
    "lastname",
    "patronymic",
    # Адрес
    "address",
    "street",
    "city",
    # Идентификаторы
    "inn",
    "guid",
    "snils",
    "passport",
    "ogrn",
    "kpp",
    # Банковские реквизиты
    "account",
    "bik",
    "card",
    "iban",
    # Учётные данные
    "login",
    "username",
    "password",
    "token",
    "secret",
    # Сетевые идентификаторы
    "url",
    "domain",
    "ip",
    "host",
}


def drop_sensitive_values(
    logger: Any,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    for key in list(event_dict.keys()):
        if key.lower() in SENSITIVE_KEYS:
            event_dict[key] = "[REDACTED]"

    return event_dict


def configure_logging(
    level: str = "INFO",
    json_logs: bool = False,
) -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    processors: list[Any] = [
        drop_sensitive_values,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(level),
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    return structlog.get_logger(name)
