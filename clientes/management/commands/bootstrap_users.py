import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crea las cuentas iniciales superuser, admin y test si todavía no existen."

    def handle(self, *args, **options):
        password = os.environ.get("INITIAL_USERS_PASSWORD", "")
        if not password or password == "change-this-locally":
            raise CommandError(
                "Configurá INITIAL_USERS_PASSWORD en .env antes de crear las cuentas iniciales."
            )

        User = get_user_model()
        administrators = Group.objects.get(name="Administradores")
        operators = Group.objects.get(name="Operadores")
        accounts = [
            {
                "username": "superuser",
                "is_staff": True,
                "is_superuser": True,
                "group": administrators,
            },
            {
                "username": "admin",
                "is_staff": True,
                "is_superuser": False,
                "group": administrators,
            },
            {
                "username": "test",
                "is_staff": False,
                "is_superuser": False,
                "group": operators,
            },
        ]

        for account in accounts:
            username = account["username"]
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "is_staff": account["is_staff"],
                    "is_superuser": account["is_superuser"],
                },
            )
            if not created:
                self.stdout.write(
                    self.style.WARNING(
                        f"El usuario '{username}' ya existe; se conserva su contraseña y configuración."
                    )
                )
                continue

            user.set_password(password)
            user.save(update_fields=["password"])
            user.groups.add(account["group"])
            self.stdout.write(self.style.SUCCESS(f"Se creó el usuario '{username}'."))
