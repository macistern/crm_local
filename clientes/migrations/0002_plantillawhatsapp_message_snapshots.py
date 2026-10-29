from django.core.validators import MaxLengthValidator
from django.db import migrations, models
import django.db.models.deletion


def snapshot_existing_messages(apps, schema_editor):
    MensajeWhatsApp = apps.get_model("clientes", "MensajeWhatsApp")
    for mensaje in MensajeWhatsApp.objects.select_related("cliente").iterator():
        if mensaje.cliente_id:
            mensaje.nombre_cliente = mensaje.cliente.nombre_completo
            mensaje.telefono_cliente = mensaje.cliente.telefono_whatsapp
        if mensaje.estado == "enviado_manual":
            mensaje.fecha_envio_manual = mensaje.fecha_hora
        mensaje.save(
            update_fields=["nombre_cliente", "telefono_cliente", "fecha_envio_manual"]
        )


def create_default_templates(apps, schema_editor):
    PlantillaWhatsApp = apps.get_model("clientes", "PlantillaWhatsApp")
    PlantillaWhatsApp.objects.bulk_create(
        [
            PlantillaWhatsApp(
                nombre="Saludo",
                texto="Hola {nombre}, ¿cómo estás? Te contactamos desde {empresa}.",
                activa=True,
            ),
            PlantillaWhatsApp(
                nombre="Seguimiento",
                texto="Hola {nombre}, queríamos hacer seguimiento de tu consulta.",
                activa=True,
            ),
            PlantillaWhatsApp(
                nombre="Consulta",
                texto="Hola {nombre}, quedamos atentos ante cualquier consulta.",
                activa=True,
            ),
        ]
    )


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlantillaWhatsApp",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nombre", models.CharField(max_length=80, unique=True, verbose_name="nombre")),
                (
                    "texto",
                    models.TextField(
                        help_text="Podés usar {nombre} y {empresa} como variables.",
                        validators=[MaxLengthValidator(4000)],
                        verbose_name="texto",
                    ),
                ),
                ("activa", models.BooleanField(default=True, verbose_name="activa")),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True, verbose_name="fecha de creación")),
                ("fecha_modificacion", models.DateTimeField(auto_now=True, verbose_name="última modificación")),
            ],
            options={
                "verbose_name": "plantilla de WhatsApp",
                "verbose_name_plural": "plantillas de WhatsApp",
                "ordering": ["nombre"],
            },
        ),
        migrations.AddField(
            model_name="mensajewhatsapp",
            name="nombre_cliente",
            field=models.CharField(blank=True, max_length=150, verbose_name="nombre del cliente"),
        ),
        migrations.AddField(
            model_name="mensajewhatsapp",
            name="telefono_cliente",
            field=models.CharField(blank=True, max_length=15, verbose_name="teléfono del cliente"),
        ),
        migrations.AddField(
            model_name="mensajewhatsapp",
            name="fecha_envio_manual",
            field=models.DateTimeField(blank=True, null=True, verbose_name="fecha de envío manual"),
        ),
        migrations.AddField(
            model_name="mensajewhatsapp",
            name="plantilla",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="mensajes",
                to="clientes.plantillawhatsapp",
            ),
        ),
        migrations.RunPython(snapshot_existing_messages, migrations.RunPython.noop),
        migrations.RunPython(create_default_templates, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="mensajewhatsapp",
            name="cliente",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="mensajes",
                to="clientes.cliente",
            ),
        ),
    ]
