import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import clientes.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Etiqueta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=40, unique=True, verbose_name="nombre")),
            ],
            options={
                "verbose_name": "etiqueta",
                "verbose_name_plural": "etiquetas",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="Cliente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre_completo", models.CharField(max_length=150, verbose_name="nombre completo")),
                (
                    "telefono_whatsapp",
                    models.CharField(
                        help_text="Formato internacional, sólo dígitos. Ejemplo: 5491123456789",
                        max_length=15,
                        validators=[clientes.validators.validate_international_phone],
                        verbose_name="teléfono WhatsApp",
                    ),
                ),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="email")),
                ("empresa", models.CharField(blank=True, max_length=120, verbose_name="empresa")),
                ("estado", models.CharField(choices=[("activo", "Activo"), ("inactivo", "Inactivo")], default="activo", max_length=8, verbose_name="estado")),
                ("notas", models.TextField(blank=True, validators=[django.core.validators.MaxLengthValidator(5000)], verbose_name="notas")),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True, verbose_name="fecha de creación")),
                ("fecha_modificacion", models.DateTimeField(auto_now=True, verbose_name="última modificación")),
                ("etiquetas", models.ManyToManyField(blank=True, related_name="clientes", to="clientes.etiqueta")),
            ],
            options={
                "verbose_name": "cliente",
                "verbose_name_plural": "clientes",
                "ordering": ["-fecha_creacion"],
                "permissions": [("deactivate_cliente", "Puede desactivar clientes")],
            },
        ),
        migrations.CreateModel(
            name="MensajeWhatsApp",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("texto", models.TextField(validators=[django.core.validators.MaxLengthValidator(4000)], verbose_name="texto del mensaje")),
                ("fecha_hora", models.DateTimeField(auto_now_add=True, verbose_name="fecha y hora")),
                ("estado", models.CharField(choices=[("borrador", "Borrador"), ("abierto_en_whatsapp", "Abierto en WhatsApp"), ("enviado_manual", "Enviado manualmente")], default="borrador", max_length=24, verbose_name="estado")),
                ("cliente", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="mensajes", to="clientes.cliente")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="mensajes_whatsapp", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "mensaje de WhatsApp",
                "verbose_name_plural": "mensajes de WhatsApp",
                "ordering": ["-fecha_hora"],
            },
        ),
    ]
