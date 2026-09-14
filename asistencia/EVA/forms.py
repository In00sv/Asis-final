import re

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import (
    Usuario,
    Justificacion,
    Asistencia
)


class RegistroUsuarioForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        label="Correo electrónico"
    )

    rut = forms.CharField(
        max_length=12,
        required=True,
        label="RUT"
    )

    class Meta:
        model = Usuario
        fields = [
            "username",
            "email",
            "rut",
            "password1",
            "password2",
        ]

    def clean_rut(self):

        rut = self.cleaned_data["rut"].strip().upper()

        rut_limpio = re.sub(
            r"[^0-9K]",
            "",
            rut
        )

        if not re.fullmatch(
            r"\d{7,8}[0-9K]",
            rut_limpio
        ):
            raise forms.ValidationError(
                "Ingrese un RUT válido."
            )

        return rut

    def save(self, commit=True):

        usuario = super().save(commit=False)

        # Los registros públicos son estudiantes.
        usuario.rol = "estudiante"

        if commit:
            usuario.save()

        return usuario


class JustificacionForm(forms.ModelForm):

    class Meta:
        model = Justificacion

        fields = [
            "fecha_inasistencia",
            "motivo",
            "descripcion",
            "documento",
        ]

        widgets = {
            "fecha_inasistencia": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),

            "motivo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Motivo de la inasistencia",
                }
            ),

            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Descripción de la situación",
                }
            ),

            "documento": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.jpg,.jpeg,.png",
                }
            ),
        }

    def clean_fecha_inasistencia(self):

        fecha = self.cleaned_data["fecha_inasistencia"]

        if fecha > __import__("datetime").date.today():
            raise forms.ValidationError(
                "La fecha de inasistencia no puede ser futura."
            )

        return fecha


class ValidacionJustificacionForm(forms.ModelForm):

    class Meta:
        model = Justificacion

        fields = [
            "estado",
            "comentarios_validador",
        ]

        widgets = {

            "estado": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "comentarios_validador": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Ingrese sus comentarios",
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        estado = cleaned_data.get("estado")

        comentarios = (
            cleaned_data.get("comentarios_validador")
            or ""
        ).strip()

        if estado == "rechazada" and not comentarios:

            self.add_error(
                "comentarios_validador",
                "Debe ingresar un comentario al rechazar "
                "una justificación."
            )

        return cleaned_data


class AsistenciaForm(forms.ModelForm):

    class Meta:
        model = Asistencia

        fields = [
            "usuario",
            "fecha",
            "estado",
        ]

        widgets = {

            "usuario": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "fecha": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),

            "estado": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["usuario"].queryset = (
            Usuario.objects
            .filter(rol="estudiante")
            .order_by("username")
        )