from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from clientes.models import Cliente, Etiqueta, MensajeWhatsApp, PlantillaWhatsApp


class Command(BaseCommand):
    help = "Crea los grupos Administradores y Operadores con permisos de la aplicación."

    def handle(self, *args, **options):
        permissions = Permission.objects.filter(
            content_type__app_label="clientes",
            content_type__model__in=[
                Cliente._meta.model_name,
                Etiqueta._meta.model_name,
                MensajeWhatsApp._meta.model_name,
                PlantillaWhatsApp._meta.model_name,
            ],
        )
        administrators, _ = Group.objects.get_or_create(name="Administradores")
        administrators.permissions.set(permissions)

        operators, _ = Group.objects.get_or_create(name="Operadores")
        operators.permissions.set(
            permissions.filter(
                codename__in=[
                    "view_cliente",
                    "add_cliente",
                    "change_cliente",
                    "deactivate_cliente",
                    "view_etiqueta",
                    "view_mensajewhatsapp",
                    "add_mensajewhatsapp",
                    "change_mensajewhatsapp",
                    "view_plantillawhatsapp",
                ]
            )
        )
        self.stdout.write(self.style.SUCCESS("Roles Administradores y Operadores configurados."))
