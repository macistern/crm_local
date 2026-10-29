from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models

from .validators import validate_international_phone


class Etiqueta(models.Model):
    nombre = models.CharField("nombre", max_length=40, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "etiqueta"
        verbose_name_plural = "etiquetas"

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        INACTIVO = "inactivo", "Inactivo"

    nombre_completo = models.CharField("nombre completo", max_length=150)
    telefono_whatsapp = models.CharField(
        "teléfono WhatsApp",
        max_length=15,
        validators=[validate_international_phone],
        help_text="Formato internacional, sólo dígitos. Ejemplo: 5491123456789",
    )
    email = models.EmailField("email", blank=True)
    empresa = models.CharField("empresa", max_length=120, blank=True)
    etiquetas = models.ManyToManyField(Etiqueta, blank=True, related_name="clientes")
    estado = models.CharField("estado", max_length=8, choices=Estado.choices, default=Estado.ACTIVO)
    notas = models.TextField("notas", blank=True, validators=[MaxLengthValidator(5000)])
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    fecha_modificacion = models.DateTimeField("última modificación", auto_now=True)

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        permissions = [("deactivate_cliente", "Puede desactivar clientes")]

    def __str__(self):
        return self.nombre_completo


class MensajeWhatsApp(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        ABIERTO_EN_WHATSAPP = "abierto_en_whatsapp", "Abierto en WhatsApp"
        ENVIADO_MANUAL = "enviado_manual", "Enviado manualmente"

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mensajes",
    )
    nombre_cliente = models.CharField("nombre del cliente", max_length=150, blank=True)
    telefono_cliente = models.CharField("teléfono del cliente", max_length=15, blank=True)
    fecha_envio_manual = models.DateTimeField("fecha de envío manual", null=True, blank=True)
    plantilla = models.ForeignKey(
        "PlantillaWhatsApp",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mensajes",
    )
    texto = models.TextField("texto del mensaje", validators=[MaxLengthValidator(4000)])
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="mensajes_whatsapp",
    )
    fecha_hora = models.DateTimeField("fecha y hora", auto_now_add=True)
    estado = models.CharField(
        "estado",
        max_length=24,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )

    class Meta:
        ordering = ["-fecha_hora"]
        verbose_name = "mensaje de WhatsApp"
        verbose_name_plural = "mensajes de WhatsApp"

    def __str__(self):
        return f"{self.nombre_cliente or 'Cliente eliminado'} - {self.get_estado_display()} - {self.fecha_hora:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        if self.cliente_id:
            self.nombre_cliente = self.cliente.nombre_completo
            self.telefono_cliente = self.cliente.telefono_whatsapp
        super().save(*args, **kwargs)


class PlantillaWhatsApp(models.Model):
    nombre = models.CharField("nombre", max_length=80, unique=True)
    texto = models.TextField(
        "texto",
        validators=[MaxLengthValidator(4000)],
        help_text="Podés usar {nombre} y {empresa} como variables.",
    )
    activa = models.BooleanField("activa", default=True)
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    fecha_modificacion = models.DateTimeField("última modificación", auto_now=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "plantilla de WhatsApp"
        verbose_name_plural = "plantillas de WhatsApp"

    def __str__(self):
        return self.nombre
