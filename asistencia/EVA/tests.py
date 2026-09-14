from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import (
    Asistencia,
    Justificacion,
    Usuario
)


class UsuarioTestCase(TestCase):

    def setUp(self):

        self.estudiante = Usuario.objects.create_user(
            username="estudiante_test",
            password="ClaveSegura123!",
            email="estudiante@test.cl",
            rut="12345678-5",
            rol="estudiante"
        )

        self.validador = Usuario.objects.create_user(
            username="validador_test",
            password="ClaveSegura123!",
            email="validador@test.cl",
            rut="12345679-3",
            rol="validador"
        )

        self.receptor = Usuario.objects.create_user(
            username="receptor_test",
            password="ClaveSegura123!",
            email="receptor@test.cl",
            rut="12345670-1",
            rol="receptor"
        )


class AutenticacionTestCase(UsuarioTestCase):

    def test_login_estudiante(self):

        respuesta = self.client.post(
            reverse("login"),
            {
                "username": "estudiante_test",
                "password": "ClaveSegura123!"
            }
        )

        self.assertRedirects(
            respuesta,
            reverse("home")
        )


    def test_login_incorrecto(self):

        respuesta = self.client.post(
            reverse("login"),
            {
                "username": "estudiante_test",
                "password": "password_incorrecta"
            }
        )

        self.assertEqual(
            respuesta.status_code,
            200
        )

        self.assertContains(
            respuesta,
            "Usuario o contraseña incorrectos."
        )


    def test_logout(self):

        self.client.login(
            username="estudiante_test",
            password="ClaveSegura123!"
        )

        respuesta = self.client.post(
            reverse("logout")
        )

        self.assertRedirects(
            respuesta,
            reverse("login")
        )


class AutorizacionTestCase(UsuarioTestCase):

    def test_estudiante_puede_crear_justificacion(self):

        self.client.login(
            username="estudiante_test",
            password="ClaveSegura123!"
        )

        respuesta = self.client.get(
            reverse("justificar_inasistencia")
        )

        self.assertEqual(
            respuesta.status_code,
            200
        )


    def test_validador_no_puede_crear_justificacion(self):

        self.client.login(
            username="validador_test",
            password="ClaveSegura123!"
        )

        respuesta = self.client.get(
            reverse("justificar_inasistencia")
        )

        self.assertEqual(
            respuesta.status_code,
            403
        )


    def test_receptor_no_puede_crear_justificacion(self):

        self.client.login(
            username="receptor_test",
            password="ClaveSegura123!"
        )

        respuesta = self.client.get(
            reverse("justificar_inasistencia")
        )

        self.assertEqual(
            respuesta.status_code,
            403
        )


    def test_estudiante_no_puede_ver_panel_validador(self):

        self.client.login(
            username="estudiante_test",
            password="ClaveSegura123!"
        )

        respuesta = self.client.get(
            reverse("panel_validador")
        )

        self.assertEqual(
            respuesta.status_code,
            403
        )


    def test_estudiante_no_puede_ver_panel_receptor(self):

        self.client.login(
            username="estudiante_test",
            password="ClaveSegura123!"
        )

        respuesta = self.client.get(
            reverse("panel_receptor")
        )

        self.assertEqual(
            respuesta.status_code,
            403
        )


class JustificacionTestCase(UsuarioTestCase):

    def test_crear_justificacion(self):

        self.client.login(
            username="estudiante_test",
            password="ClaveSegura123!"
        )

        respuesta = self.client.post(
            reverse("justificar_inasistencia"),
            {
                "fecha_inasistencia": "2026-09-10",
                "motivo": "Enfermedad",
                "descripcion": "No pude asistir.",
            }
        )

        self.assertRedirects(
            respuesta,
            reverse("historial_justificaciones")
        )

        self.assertEqual(
            Justificacion.objects.count(),
            1
        )

        justificacion = (
            Justificacion.objects.first()
        )

        self.assertEqual(
            justificacion.usuario,
            self.estudiante
        )

        self.assertEqual(
            justificacion.estado,
            "pendiente"
        )


    def test_estudiante_solo_ve_sus_justificaciones(self):

        Justificacion.objects.create(
            usuario=self.estudiante,
            fecha_inasistencia=date(2026, 9, 10),
            motivo="Motivo estudiante",
            descripcion="Descripción"
        )

        otro = Usuario.objects.create_user(
            username="otro_estudiante",
            password="ClaveSegura123!",
            rut="12345671-K",
            rol="estudiante"
        )

        Justificacion.objects.create(
            usuario=otro,
            fecha_inasistencia=date(2026, 9, 11),
            motivo="Otro motivo",
            descripcion="Otra descripción"
        )

        self.client.login(
            username="estudiante_test",
            password="ClaveSegura123!"
        )

        respuesta = self.client.get(
            reverse("historial_justificaciones")
        )

        self.assertEqual(
            respuesta.context["justificaciones"].count(),
            1
        )


class ValidacionTestCase(UsuarioTestCase):

    def setUp(self):

        super().setUp()

        self.justificacion = Justificacion.objects.create(
            usuario=self.estudiante,
            fecha_inasistencia=date(2026, 9, 10),
            motivo="Enfermedad",
            descripcion="No pude asistir."
        )


    def test_validador_puede_revisar(self):

        self.client.login(
            username="validador_test",
            password="ClaveSegura123!"
        )

        respuesta = self.client.get(
            reverse(
                "revisar_justificacion",
                args=[self.justificacion.pk]
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200
        )


    def test_validador_puede_aprobar(self):

        self.client.login(
            username="validador_test",
            password="ClaveSegura123!"
        )

        respuesta = self.client.post(
            reverse(
                "revisar_justificacion",
                args=[self.justificacion.pk]
            ),
            {
                "estado": "aprobada",
                "comentarios_validador": "Antecedentes correctos."
            }
        )

        self.assertRedirects(
            respuesta,
            reverse("panel_validador")
        )

        self.justificacion.refresh_from_db()

        self.assertEqual(
            self.justificacion.estado,
            "aprobada"
        )


    def test_validador_debe_comentar_al_rechazar(self):

        self.client.login(
            username="validador_test",
            password="ClaveSegura123!"
        )

        respuesta = self.client.post(
            reverse(
                "revisar_justificacion",
                args=[self.justificacion.pk]
            ),
            {
                "estado": "rechazada",
                "comentarios_validador": ""
            }
        )

        self.assertEqual(
            respuesta.status_code,
            200
        )

        self.justificacion.refresh_from_db()

        self.assertEqual(
            self.justificacion.estado,
            "pendiente"
        )


class AsistenciaTestCase(UsuarioTestCase):

    def test_receptor_puede_registrar_asistencia(self):

        self.client.login(
            username="receptor_test",
            password="ClaveSegura123!"
        )

        respuesta = self.client.post(
            reverse("registrar_asistencia"),
            {
                "usuario": self.estudiante.pk,
                "fecha": "2026-09-12",
                "estado": "Presente"
            }
        )

        self.assertRedirects(
            respuesta,
            reverse("panel_receptor")
        )

        self.assertEqual(
            Asistencia.objects.count(),
            1
        )


    def test_estudiante_no_puede_registrar_asistencia(self):

        self.client.login(
            username="estudiante_test",
            password="ClaveSegura123!"
        )

        respuesta = self.client.get(
            reverse("registrar_asistencia")
        )

        self.assertEqual(
            respuesta.status_code,
            403
        )


class SeguridadArchivosTestCase(UsuarioTestCase):

    def test_archivo_pdf_valido(self):

        self.client.login(
            username="estudiante_test",
            password="ClaveSegura123!"
        )

        archivo = SimpleUploadedFile(
            "documento.pdf",
            b"%PDF-1.4 documento de prueba",
            content_type="application/pdf"
        )

        respuesta = self.client.post(
            reverse("justificar_inasistencia"),
            {
                "fecha_inasistencia": "2026-09-10",
                "motivo": "Enfermedad",
                "descripcion": "Documento válido.",
                "documento": archivo,
            }
        )

        self.assertRedirects(
            respuesta,
            reverse("historial_justificaciones")
        )