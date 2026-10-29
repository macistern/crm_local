from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("clientes/", views.lista_clientes, name="lista_clientes"),
    path("clientes/nuevo/", views.crear_cliente, name="crear_cliente"),
    path("clientes/<int:pk>/", views.detalle_cliente, name="detalle_cliente"),
    path("clientes/<int:pk>/editar/", views.editar_cliente, name="editar_cliente"),
    path("clientes/<int:pk>/desactivar/", views.desactivar_cliente, name="desactivar_cliente"),
    path("clientes/<int:pk>/eliminar/", views.eliminar_cliente, name="eliminar_cliente"),
    path("clientes/<int:pk>/whatsapp/", views.enviar_whatsapp, name="enviar_whatsapp"),
    path("mensajes/", views.historial_mensajes, name="historial_mensajes"),
    path("mensajes/<int:pk>/marcar-enviado/", views.marcar_mensaje_enviado, name="marcar_mensaje_enviado"),
    path("plantillas/", views.lista_plantillas, name="lista_plantillas"),
    path("plantillas/nueva/", views.crear_plantilla, name="crear_plantilla"),
    path("plantillas/<int:pk>/editar/", views.editar_plantilla, name="editar_plantilla"),
    path("plantillas/<int:pk>/eliminar/", views.eliminar_plantilla, name="eliminar_plantilla"),
    path("configuracion/", views.configuracion, name="configuracion"),
]
