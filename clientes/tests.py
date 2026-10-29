from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ClienteForm
from .models import Cliente, Etiqueta, MensajeWhatsApp, PlantillaWhatsApp


class BootstrapUsersTests(TestCase):
    def setUp(self):
        call_command("setup_roles", verbosity=0)

    @patch.dict("os.environ", {"INITIAL_USERS_PASSWORD": "test-bootstrap-password"})
    def test_bootstrap_creates_three_users_with_requested_password_and_roles(self):
        call_command("bootstrap_users", verbosity=0)
        User = get_user_model()
        superuser = User.objects.get(username="superuser")
        admin = User.objects.get(username="admin")
        test_user = User.objects.get(username="test")

        for user in (superuser, admin, test_user):
            self.assertTrue(user.check_password("test-bootstrap-password"))
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(admin.is_staff)
        self.assertFalse(admin.is_superuser)
        self.assertFalse(test_user.is_staff)
        self.assertFalse(test_user.is_superuser)
        self.assertTrue(superuser.groups.filter(name="Administradores").exists())
        self.assertTrue(admin.groups.filter(name="Administradores").exists())
        self.assertTrue(test_user.groups.filter(name="Operadores").exists())

    @patch.dict("os.environ", {"INITIAL_USERS_PASSWORD": "test-bootstrap-password"})
    def test_bootstrap_is_idempotent_and_does_not_reset_existing_password(self):
        call_command("bootstrap_users", verbosity=0)
        admin = get_user_model().objects.get(username="admin")
        admin.set_password("custom-admin-password")
        admin.save(update_fields=["password"])

        call_command("bootstrap_users", verbosity=0)
        admin.refresh_from_db()

        self.assertTrue(admin.check_password("custom-admin-password"))

    @patch.dict("os.environ", {}, clear=True)
    def test_bootstrap_requires_password_environment_variable(self):
        with self.assertRaises(CommandError):
            call_command("bootstrap_users", verbosity=0)


class ClienteModelTests(TestCase):
    def test_cliente_defaults_to_active_and_keeps_creation_timestamp(self):
        cliente = Cliente.objects.create(
            nombre_completo="Ana Pérez",
            telefono_whatsapp="5491123456789",
        )
        self.assertEqual(cliente.estado, Cliente.Estado.ACTIVO)
        self.assertIsNotNone(cliente.fecha_creacion)
        self.assertIsNotNone(cliente.fecha_modificacion)
        self.assertEqual(str(cliente), "Ana Pérez")

    def test_phone_form_normalizes_international_format(self):
        form = ClienteForm(
            data={
                "nombre_completo": "Ana Pérez",
                "telefono_whatsapp": "+54 9 (11) 2345-6789",
                "email": "",
                "empresa": "",
                "estado": Cliente.Estado.ACTIVO,
                "notas": "",
                "etiquetas": [],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        cliente = form.save()
        self.assertEqual(cliente.telefono_whatsapp, "5491123456789")

    def test_phone_rejects_non_digit_or_non_international_values(self):
        for phone in ("12345", "05491123456789", "54911abc56789"):
            with self.subTest(phone=phone):
                form = ClienteForm(
                    data={
                        "nombre_completo": "Ana Pérez",
                        "telefono_whatsapp": phone,
                        "email": "",
                        "empresa": "",
                        "estado": Cliente.Estado.ACTIVO,
                        "notas": "",
                        "etiquetas": [],
                    }
                )
                self.assertFalse(form.is_valid())
                self.assertIn("telefono_whatsapp", form.errors)


class WhatsAppTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="operador",
            password="una-clave-de-prueba-segura",
        )
        group = Group.objects.create(name="Operadores")
        group.permissions.add(
            Permission.objects.get(codename="view_cliente"),
            Permission.objects.get(codename="add_cliente"),
            Permission.objects.get(codename="change_cliente"),
            Permission.objects.get(codename="deactivate_cliente"),
            Permission.objects.get(codename="view_mensajewhatsapp"),
            Permission.objects.get(codename="add_mensajewhatsapp"),
            Permission.objects.get(codename="change_mensajewhatsapp"),
            Permission.objects.get(codename="view_plantillawhatsapp"),
        )
        self.user.groups.add(group)
        self.cliente = Cliente.objects.create(
            nombre_completo="Ana Pérez",
            telefono_whatsapp="5491123456789",
        )

    def test_message_is_created_as_opened_in_whatsapp(self):
        self.client.force_login(self.user)
        plantilla = PlantillaWhatsApp.objects.get(nombre="Saludo")
        response = self.client.post(
            reverse("enviar_whatsapp", args=[self.cliente.pk]),
            {"texto": "Hola Ana, ¿cómo estás?", "plantilla": plantilla.pk},
        )
        mensaje = MensajeWhatsApp.objects.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mensaje.cliente, self.cliente)
        self.assertEqual(mensaje.usuario, self.user)
        self.assertEqual(mensaje.plantilla, plantilla)
        self.assertEqual(mensaje.estado, MensajeWhatsApp.Estado.ABIERTO_EN_WHATSAPP)
        launch_url = response.context["whatsapp_url"]
        self.assertEqual(urlparse(launch_url).netloc, "wa.me")
        self.assertEqual(urlparse(launch_url).path, "/5491123456789")
        self.assertEqual(parse_qs(urlparse(launch_url).query)["text"], ["Hola Ana, ¿cómo estás?"])

    def test_anonymous_users_are_redirected_from_client_pages(self):
        response = self.client.get(reverse("lista_clientes"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('lista_clientes')}")

    def test_user_without_permission_cannot_create_client(self):
        viewer = get_user_model().objects.create_user(
            username="solo-lectura",
            password="una-clave-de-prueba-segura",
        )
        viewer.user_permissions.add(Permission.objects.get(codename="view_cliente"))
        self.client.force_login(viewer)
        response = self.client.post(
            reverse("crear_cliente"),
            {
                "nombre_completo": "Otra persona",
                "telefono_whatsapp": "5491123456788",
                "estado": Cliente.Estado.ACTIVO,
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Cliente.objects.filter(telefono_whatsapp="5491123456788").exists())

    def test_operator_can_create_and_edit_a_client(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("crear_cliente"),
            {
                "nombre_completo": "Nueva persona",
                "telefono_whatsapp": "5491123456788",
                "estado": Cliente.Estado.ACTIVO,
                "etiquetas": [],
            },
        )
        nuevo_cliente = Cliente.objects.get(telefono_whatsapp="5491123456788")
        self.assertRedirects(response, reverse("detalle_cliente", args=[nuevo_cliente.pk]))

        response = self.client.post(
            reverse("editar_cliente", args=[nuevo_cliente.pk]),
            {
                "nombre_completo": "Persona editada",
                "telefono_whatsapp": "5491123456788",
                "estado": Cliente.Estado.ACTIVO,
                "etiquetas": [],
            },
        )
        nuevo_cliente.refresh_from_db()
        self.assertRedirects(response, reverse("detalle_cliente", args=[nuevo_cliente.pk]))
        self.assertEqual(nuevo_cliente.nombre_completo, "Persona editada")

    def test_operator_can_mark_message_as_manually_sent(self):
        mensaje = MensajeWhatsApp.objects.create(
            cliente=self.cliente,
            texto="Hola",
            usuario=self.user,
            estado=MensajeWhatsApp.Estado.ABIERTO_EN_WHATSAPP,
        )
        self.client.force_login(self.user)
        response = self.client.post(reverse("marcar_mensaje_enviado", args=[mensaje.pk]))
        mensaje.refresh_from_db()
        self.assertRedirects(response, reverse("detalle_cliente", args=[self.cliente.pk]))
        self.assertEqual(mensaje.estado, MensajeWhatsApp.Estado.ENVIADO_MANUAL)

    def test_operator_can_deactivate_without_deleting_client(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("desactivar_cliente", args=[self.cliente.pk]))
        self.cliente.refresh_from_db()
        self.assertRedirects(response, reverse("detalle_cliente", args=[self.cliente.pk]))
        self.assertEqual(self.cliente.estado, Cliente.Estado.INACTIVO)
        self.assertTrue(Cliente.objects.filter(pk=self.cliente.pk).exists())

    def test_admin_can_delete_client_after_explicit_confirmation_and_keep_history(self):
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()
        mensaje = MensajeWhatsApp.objects.create(
            cliente=self.cliente,
            texto="Mensaje guardado",
            usuario=self.user,
            estado=MensajeWhatsApp.Estado.ENVIADO_MANUAL,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("eliminar_cliente", args=[self.cliente.pk]),
            {"confirmar": ""},
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Cliente.objects.filter(pk=self.cliente.pk).exists())

        response = self.client.post(
            reverse("eliminar_cliente", args=[self.cliente.pk]),
            {"confirmar": "si"},
        )
        self.assertRedirects(response, reverse("lista_clientes"))
        self.assertFalse(Cliente.objects.filter(pk=self.cliente.pk).exists())
        mensaje.refresh_from_db()
        self.assertIsNone(mensaje.cliente)
        self.assertEqual(mensaje.nombre_cliente, "Ana Pérez")
        self.assertEqual(mensaje.telefono_cliente, "5491123456789")
        self.assertContains(
            self.client.get(reverse("historial_mensajes")),
            "Ana Pérez",
        )

    def test_operator_can_view_sent_history_but_not_edit_templates(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("lista_plantillas"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Saludo")
        response = self.client.get(reverse("detalle_cliente", args=[self.cliente.pk]))
        self.assertContains(response, "Plantillas disponibles")
        self.assertContains(response, 'data-plantilla-id="')
        self.assertEqual(
            self.client.post(reverse("crear_plantilla"), {}).status_code,
            403,
        )

        mensaje = MensajeWhatsApp.objects.create(
            cliente=self.cliente,
            texto="Enviado",
            usuario=self.user,
            estado=MensajeWhatsApp.Estado.ENVIADO_MANUAL,
        )
        mensaje.fecha_envio_manual = timezone.now()
        mensaje.save(update_fields=["fecha_envio_manual"])
        response = self.client.get(reverse("historial_mensajes"))
        self.assertContains(response, "Enviado")
        self.assertContains(response, "Ana Pérez")

    def test_htmx_client_search_returns_results_fragment(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("lista_clientes"),
            {"q": "Ana"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ana Pérez")
        self.assertNotContains(response, "<html")


class EtiquetaTests(TestCase):
    def test_customer_can_have_multiple_tags(self):
        cliente = Cliente.objects.create(
            nombre_completo="Ana Pérez",
            telefono_whatsapp="5491123456789",
        )
        etiquetas = [Etiqueta.objects.create(nombre=n) for n in ("VIP", "Nuevo")]
        cliente.etiquetas.add(*etiquetas)
        self.assertEqual(cliente.etiquetas.count(), 2)
