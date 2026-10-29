from django.contrib import admin

from .models import Cliente, Etiqueta, MensajeWhatsApp, PlantillaWhatsApp


@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    search_fields = ["nombre"]
    ordering = ["nombre"]


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["nombre_completo", "telefono_whatsapp", "empresa", "estado", "fecha_creacion"]
    list_filter = ["estado", "etiquetas"]
    search_fields = ["nombre_completo", "telefono_whatsapp", "email", "empresa"]
    filter_horizontal = ["etiquetas"]
    actions = ["desactivar_clientes"]

    @admin.action(description="Desactivar clientes seleccionados")
    def desactivar_clientes(self, request, queryset):
        queryset.update(estado=Cliente.Estado.INACTIVO)

@admin.register(MensajeWhatsApp)
class MensajeWhatsAppAdmin(admin.ModelAdmin):
    list_display = ["nombre_cliente", "telefono_cliente", "usuario", "estado", "fecha_hora"]
    list_filter = ["estado", "fecha_hora"]
    search_fields = ["nombre_cliente", "telefono_cliente", "texto", "usuario__username"]
    readonly_fields = ["fecha_hora", "fecha_envio_manual", "nombre_cliente", "telefono_cliente"]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PlantillaWhatsApp)
class PlantillaWhatsAppAdmin(admin.ModelAdmin):
    list_display = ["nombre", "activa", "fecha_modificacion"]
    list_filter = ["activa"]
    search_fields = ["nombre", "texto"]
