from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from clientes.models import Cliente, Etiqueta


class Command(BaseCommand):
    help = "Carga clientes y etiquetas de ejemplo sin modificar usuarios existentes."

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            self.stdout.write(
                self.style.WARNING(
                    "No hay superusuario todavía; los datos demo se cargarán igual."
                )
            )
        etiquetas = {
            nombre: Etiqueta.objects.get_or_create(nombre=nombre)[0]
            for nombre in ("Prospecto", "Prioritario", "Seguimiento")
        }
        ejemplos = [
            {
                "nombre_completo": "Lucía Fernández",
                "telefono_whatsapp": "5491123456701",
                "email": "lucia@example.com",
                "empresa": "Estudio Fernández",
                "tags": ["Prospecto", "Seguimiento"],
            },
            {
                "nombre_completo": "Mateo González",
                "telefono_whatsapp": "5491123456702",
                "email": "mateo@example.com",
                "empresa": "González y Asociados",
                "tags": ["Prioritario"],
            },
            {
                "nombre_completo": "Sofía Romero",
                "telefono_whatsapp": "5491123456703",
                "email": "",
                "empresa": "",
                "tags": ["Seguimiento"],
            },
        ]
        for datos in ejemplos:
            tag_names = datos.pop("tags")
            cliente, _ = Cliente.objects.get_or_create(
                telefono_whatsapp=datos["telefono_whatsapp"],
                defaults=datos,
            )
            cliente.etiquetas.set(etiquetas[nombre] for nombre in tag_names)
        self.stdout.write(self.style.SUCCESS("Datos de ejemplo cargados."))
