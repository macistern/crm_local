from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ClienteForm, MensajeWhatsAppForm, PlantillaWhatsAppForm
from .models import Cliente, Etiqueta, MensajeWhatsApp, PlantillaWhatsApp
from .permissions import administrator_required


@login_required
@permission_required("clientes.view_cliente", raise_exception=True)
def inicio(request):
    ahora = timezone.localtime()
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    context = {
        "clientes_activos": Cliente.objects.filter(estado=Cliente.Estado.ACTIVO).count(),
        "clientes_nuevos_mes": Cliente.objects.filter(fecha_creacion__gte=inicio_mes).count(),
        "mensajes_mes": MensajeWhatsApp.objects.filter(fecha_hora__gte=inicio_mes).count(),
        "ultimos_clientes": Cliente.objects.select_related().prefetch_related("etiquetas")[:5],
    }
    return render(request, "clientes/inicio.html", context)


@login_required
@permission_required("clientes.view_cliente", raise_exception=True)
def lista_clientes(request):
    clientes = Cliente.objects.prefetch_related("etiquetas")
    consulta = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "")
    etiqueta = request.GET.get("etiqueta", "")
    if consulta:
        clientes = clientes.filter(
            Q(nombre_completo__icontains=consulta)
            | Q(telefono_whatsapp__icontains=consulta)
            | Q(email__icontains=consulta)
            | Q(empresa__icontains=consulta)
        )

    if estado in Cliente.Estado.values:
        clientes = clientes.filter(estado=estado)
    if etiqueta.isdigit():
        clientes = clientes.filter(etiquetas__id=int(etiqueta))
    template = (
        "clientes/partials/lista_resultados.html"
        if request.headers.get("HX-Request") == "true"
        else "clientes/lista.html"
    )
    return render(
        request,
        template,
        {
            "clientes": clientes.distinct(),
            "consulta": consulta,
            "estado_seleccionado": estado,
            "etiqueta_seleccionada": etiqueta,
            "etiquetas": Etiqueta.objects.all(),
        },
    )


@login_required
@permission_required("clientes.add_cliente", raise_exception=True)
def crear_cliente(request):
    form = ClienteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cliente = form.save()
        messages.success(request, "El cliente se creó correctamente.")
        return redirect("detalle_cliente", pk=cliente.pk)
    return render(request, "clientes/formulario.html", {"form": form, "titulo": "Nuevo cliente"})


@login_required
@permission_required("clientes.view_cliente", raise_exception=True)
def detalle_cliente(request, pk):
    cliente = get_object_or_404(
        Cliente.objects.prefetch_related("etiquetas", "mensajes__usuario"),
        pk=pk,
    )
    mensaje_form = MensajeWhatsAppForm()
    return render(
        request,
        "clientes/detalle.html",
        {
            "cliente": cliente,
            "mensaje_form": mensaje_form,
            "plantillas_activas": mensaje_form.fields["plantilla"].queryset,
        },
    )


@login_required
@permission_required("clientes.change_cliente", raise_exception=True)
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=cliente)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Los datos del cliente se actualizaron.")
        return redirect("detalle_cliente", pk=cliente.pk)
    return render(
        request,
        "clientes/formulario.html",
        {"form": form, "titulo": "Editar cliente", "cliente": cliente},
    )


@login_required
@permission_required("clientes.deactivate_cliente", raise_exception=True)
def desactivar_cliente(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.estado = Cliente.Estado.INACTIVO
    cliente.save(update_fields=["estado", "fecha_modificacion"])
    messages.success(request, "El cliente quedó inactivo. Su historial se conservó.")
    return redirect("detalle_cliente", pk=cliente.pk)


@login_required
@permission_required("clientes.delete_cliente", raise_exception=True)
def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        if request.POST.get("confirmar") != "si":
            return render(
                request,
                "clientes/confirmar_eliminacion.html",
                {"cliente": cliente, "error_confirmacion": True},
                status=400,
            )
        nombre = cliente.nombre_completo
        cliente.delete()
        messages.success(
            request,
            f"Se eliminó el cliente {nombre}. El historial de WhatsApp se conservó.",
        )
        return redirect("lista_clientes")
    return render(request, "clientes/confirmar_eliminacion.html", {"cliente": cliente})


@login_required
@permission_required("clientes.add_mensajewhatsapp", raise_exception=True)
def enviar_whatsapp(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    cliente = get_object_or_404(Cliente, pk=pk)
    form = MensajeWhatsAppForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "clientes/detalle.html",
            {
                "cliente": cliente,
                "mensaje_form": form,
                "plantillas_activas": form.fields["plantilla"].queryset,
                "abrir_modal_whatsapp": True,
            },
            status=400,
        )
    mensaje = form.save(commit=False)
    mensaje.cliente = cliente
    mensaje.usuario = request.user
    mensaje.plantilla = form.cleaned_data["plantilla"]
    mensaje.estado = MensajeWhatsApp.Estado.ABIERTO_EN_WHATSAPP
    mensaje.save()
    whatsapp_url = (
        f"https://wa.me/{cliente.telefono_whatsapp}?"
        f"{urlencode({'text': mensaje.texto})}"
    )
    return render(
        request,
        "clientes/whatsapp_lanzar.html",
        {"whatsapp_url": whatsapp_url},
    )


@login_required
@permission_required("clientes.view_mensajewhatsapp", raise_exception=True)
def historial_mensajes(request):
    mensajes = MensajeWhatsApp.objects.filter(
        estado=MensajeWhatsApp.Estado.ENVIADO_MANUAL
    ).select_related("cliente", "usuario").order_by("-fecha_envio_manual", "-fecha_hora")
    consulta = request.GET.get("q", "").strip()
    if consulta:
        mensajes = mensajes.filter(
            Q(nombre_cliente__icontains=consulta)
            | Q(telefono_cliente__icontains=consulta)
            | Q(texto__icontains=consulta)
            | Q(usuario__username__icontains=consulta)
        )
    return render(
        request,
        "clientes/historial_mensajes.html",
        {"mensajes": mensajes, "consulta": consulta},
    )


@login_required
@permission_required("clientes.change_mensajewhatsapp", raise_exception=True)
def marcar_mensaje_enviado(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    mensaje = get_object_or_404(
        MensajeWhatsApp.objects.select_related("cliente"),
        pk=pk,
        estado=MensajeWhatsApp.Estado.ABIERTO_EN_WHATSAPP,
    )
    mensaje.estado = MensajeWhatsApp.Estado.ENVIADO_MANUAL
    mensaje.fecha_envio_manual = timezone.now()
    mensaje.save(update_fields=["estado", "fecha_envio_manual"])
    messages.success(request, "El mensaje se marcó como enviado manualmente.")
    if mensaje.cliente_id:
        return redirect("detalle_cliente", pk=mensaje.cliente_id)
    return redirect("historial_mensajes")


@login_required
@permission_required("clientes.view_plantillawhatsapp", raise_exception=True)
def lista_plantillas(request):
    return render(
        request,
        "clientes/plantillas_lista.html",
        {"plantillas": PlantillaWhatsApp.objects.all()},
    )


@login_required
@permission_required("clientes.add_plantillawhatsapp", raise_exception=True)
def crear_plantilla(request):
    form = PlantillaWhatsAppForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        plantilla = form.save()
        messages.success(request, "La plantilla se creó correctamente.")
        return redirect("editar_plantilla", pk=plantilla.pk)
    return render(
        request,
        "clientes/plantilla_formulario.html",
        {"form": form, "titulo": "Nueva plantilla"},
    )


@login_required
@permission_required("clientes.change_plantillawhatsapp", raise_exception=True)
def editar_plantilla(request, pk):
    plantilla = get_object_or_404(PlantillaWhatsApp, pk=pk)
    form = PlantillaWhatsAppForm(request.POST or None, instance=plantilla)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "La plantilla se actualizó correctamente.")
        return redirect("lista_plantillas")
    return render(
        request,
        "clientes/plantilla_formulario.html",
        {"form": form, "titulo": "Editar plantilla", "plantilla": plantilla},
    )


@login_required
@permission_required("clientes.delete_plantillawhatsapp", raise_exception=True)
def eliminar_plantilla(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    plantilla = get_object_or_404(PlantillaWhatsApp, pk=pk)
    nombre = plantilla.nombre
    plantilla.delete()
    messages.success(request, f"Se eliminó la plantilla {nombre}.")
    return redirect("lista_plantillas")


@login_required
@administrator_required
def configuracion(request):
    return render(request, "clientes/configuracion.html")
