import re

from django.core.exceptions import ValidationError


PHONE_PATTERN = re.compile(r"^[1-9][0-9]{7,14}$")


def validate_international_phone(value):
    if not PHONE_PATTERN.fullmatch(value):
        raise ValidationError(
            "Ingresá un teléfono internacional de 8 a 15 dígitos, sin el signo +.",
            code="invalid_phone",
        )


def normalize_phone(value):
    cleaned = re.sub(r"[\s()+.-]", "", value)
    if not re.fullmatch(r"[0-9]+", cleaned):
        raise ValidationError("El teléfono sólo puede contener dígitos, espacios, +, guiones o paréntesis.")
    validate_international_phone(cleaned)
    return cleaned
