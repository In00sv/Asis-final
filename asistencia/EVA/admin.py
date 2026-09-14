from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from EVA import views


urlpatterns = [

    # Administración
    path(
        "admin/",
        admin.site.urls
    ),

    # Autenticación
    path(
        "",
        views.login_view,
        name="login"
    ),

    path(
        "registro/",
        views.registro,
        name="registro"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),

    # Inicio
    path(
        "home/",
        views.home,
        name="home"
    ),

    # Estudiante
    path(
        "justificar/",
        views.justificar_inasistencia,
        name="justificar_inasistencia"
    ),

    path(
        "historial/",
        views.historial_justificaciones,
        name="historial_justificaciones"
    ),

    path(
        "justificacion/<int:pk>/eliminar/",
        views.eliminar_justificacion,
        name="eliminar_justificacion"
    ),

    # Validador
    path(
        "validador/",
        views.panel_validador,
        name="panel_validador"
    ),

    path(
        "validador/justificacion/<int:pk>/",
        views.revisar_justificacion,
        name="revisar_justificacion"
    ),

    # Receptor
    path(
        "receptor/",
        views.panel_receptor,
        name="panel_receptor"
    ),

    path(
        "receptor/asistencia/registrar/",
        views.registrar_asistencia,
        name="registrar_asistencia"
    ),

    path(
        "receptor/asistencia/<int:pk>/editar/",
        views.editar_asistencia,
        name="editar_asistencia"
    ),

    path(
        "receptor/asistencia/<int:pk>/eliminar/",
        views.eliminar_asistencia,
        name="eliminar_asistencia"
    ),
]


# Archivos multimedia durante desarrollo
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )