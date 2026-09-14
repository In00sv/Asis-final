from functools import wraps

from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout
)
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpResponseForbidden
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render
)
from django.views.decorators.http import require_http_methods

from .forms import (
    AsistenciaForm,
    JustificacionForm,
    RegistroUsuarioForm,
    ValidacionJustificacionForm,
)
from .models import (
    Asistencia,
    Justificacion,
)


# ==========================================================
# AUTORIZACIÓN POR ROLES
# ==========================================================

def requiere_rol(*roles):

    def decorador(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("login")

            if request.user.rol not in roles:
                return render(
                    request,
                    "403.html",
                    status=403
                )

            return view_func(
                request,
                *args,
                **kwargs
            )

        return wrapper

    return decorador


# ==========================================================
# LOGIN
# ==========================================================

@require_http_methods(["GET", "POST"])
def login_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = (
            request.POST.get("username", "")
            .strip()
        )

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if not user.is_active:

                return render(
                    request,
                    "asistencia/login.html",
                    {
                        "error": (
                            "La cuenta se encuentra "
                            "desactivada."
                        )
                    }
                )

            login(request, user)

            return redirect("home")

        return render(
            request,
            "asistencia/login.html",
            {
                "error": (
                    "Usuario o contraseña incorrectos."
                )
            }
        )

    return render(
        request,
        "asistencia/login.html"
    )


# ==========================================================
# REGISTRO
# ==========================================================

@require_http_methods(["GET", "POST"])
def registro(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        form = RegistroUsuarioForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Registro realizado correctamente. "
                "Ahora puede iniciar sesión."
            )

            return redirect("login")

    else:

        form = RegistroUsuarioForm()

    return render(
        request,
        "registro.html",
        {
            "form": form
        }
    )


# ==========================================================
# LOGOUT
# ==========================================================

@require_http_methods(["POST"])
@login_required
def logout_view(request):

    logout(request)

    return redirect("login")


# ==========================================================
# HOME
# ==========================================================

@login_required
def home(request):

    return render(
        request,
        "home.html"
    )


# ==========================================================
# ESTUDIANTE
# ==========================================================

@requiere_rol("estudiante")
def justificar_inasistencia(request):

    if request.method == "POST":

        form = JustificacionForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            justificacion = form.save(
                commit=False
            )

            justificacion.usuario = (
                request.user
            )

            justificacion.estado = "pendiente"

            justificacion.save()

            messages.success(
                request,
                "La justificación fue enviada "
                "correctamente."
            )

            return redirect(
                "historial_justificaciones"
            )

    else:

        form = JustificacionForm()

    return render(
        request,
        "justificar_inasistencia.html",
        {
            "form": form
        }
    )


@requiere_rol("estudiante")
def historial_justificaciones(request):

    justificaciones = (
        Justificacion.objects
        .filter(usuario=request.user)
        .order_by("-fecha_envio")
    )

    return render(
        request,
        "historial_justificaciones.html",
        {
            "justificaciones": justificaciones
        }
    )


@requiere_rol("estudiante")
def eliminar_justificacion(
    request,
    pk
):

    if request.method != "POST":

        return HttpResponseForbidden(
            "Método no permitido."
        )

    justificacion = get_object_or_404(
        Justificacion,
        pk=pk,
        usuario=request.user
    )

    if justificacion.estado != "pendiente":

        messages.error(
            request,
            "Solo se pueden eliminar "
            "justificaciones pendientes."
        )

        return redirect(
            "historial_justificaciones"
        )

    justificacion.delete()

    messages.success(
        request,
        "La justificación fue eliminada."
    )

    return redirect(
        "historial_justificaciones"
    )


# ==========================================================
# VALIDADOR
# ==========================================================

@requiere_rol("validador")
def panel_validador(request):

    justificaciones = (
        Justificacion.objects
        .select_related("usuario")
        .filter(estado="pendiente")
        .order_by("fecha_envio")
    )

    return render(
        request,
        "validador/panel.html",
        {
            "justificaciones": justificaciones
        }
    )


@requiere_rol("validador")
def revisar_justificacion(
    request,
    pk
):

    justificacion = get_object_or_404(
        Justificacion.objects.select_related(
            "usuario"
        ),
        pk=pk
    )

    if request.method == "POST":

        form = ValidacionJustificacionForm(
            request.POST,
            instance=justificacion
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "La justificación fue actualizada."
            )

            return redirect(
                "panel_validador"
            )

    else:

        form = ValidacionJustificacionForm(
            instance=justificacion
        )

    return render(
        request,
        "validador/revisar.html",
        {
            "justificacion": justificacion,
            "form": form
        }
    )


# ==========================================================
# RECEPTOR
# ==========================================================

@requiere_rol("receptor")
def panel_receptor(request):

    asistencias = (
        Asistencia.objects
        .select_related("usuario")
        .order_by("-fecha", "usuario__username")
    )

    return render(
        request,
        "receptor/panel.html",
        {
            "asistencias": asistencias
        }
    )


@requiere_rol("receptor")
def registrar_asistencia(request):

    if request.method == "POST":

        form = AsistenciaForm(
            request.POST
        )

        if form.is_valid():

            try:

                with transaction.atomic():

                    asistencia = form.save()

                messages.success(
                    request,
                    "La asistencia fue registrada "
                    "correctamente."
                )

                return redirect(
                    "panel_receptor"
                )

            except IntegrityError:

                form.add_error(
                    None,
                    "Ya existe un registro de asistencia "
                    "para ese estudiante y fecha."
                )

    else:

        form = AsistenciaForm()

    return render(
        request,
        "receptor/registrar.html",
        {
            "form": form
        }
    )


@requiere_rol("receptor")
def editar_asistencia(
    request,
    pk
):

    asistencia = get_object_or_404(
        Asistencia,
        pk=pk
    )

    if request.method == "POST":

        form = AsistenciaForm(
            request.POST,
            instance=asistencia
        )

        if form.is_valid():

            try:

                with transaction.atomic():

                    form.save()

                messages.success(
                    request,
                    "El registro de asistencia fue actualizado."
                )

                return redirect(
                    "panel_receptor"
                )

            except IntegrityError:

                form.add_error(
                    None,
                    "Ya existe un registro para ese "
                    "estudiante y fecha."
                )

    else:

        form = AsistenciaForm(
            instance=asistencia
        )

    return render(
        request,
        "receptor/editar.html",
        {
            "form": form,
            "asistencia": asistencia
        }
    )


@requiere_rol("receptor")
def eliminar_asistencia(
    request,
    pk
):

    if request.method != "POST":

        return HttpResponseForbidden(
            "Método no permitido."
        )

    asistencia = get_object_or_404(
        Asistencia,
        pk=pk
    )

    asistencia.delete()

    messages.success(
        request,
        "El registro de asistencia fue eliminado."
    )

    return redirect(
        "panel_receptor"
    )