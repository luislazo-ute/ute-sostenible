from odoo import http
from odoo.http import request


class PlantillaPesajeController(http.Controller):
    @http.route(
        "/ute_sostenible/plantilla_pesaje/pdf",
        type="http",
        auth="user",
    )
    def descargar_plantilla_pesaje(self, fecha=None, campus_id=None, **kwargs):
        usuario = request.env.user
        if not (
            usuario.has_group("ute_sostenible.grupo_usuario_ute_sostenible")
            or usuario.has_group("ute_sostenible.grupo_administrador_ute_sostenible")
        ):
            return request.not_found()

        report = request.env.ref("ute_sostenible.accion_reporte_plantilla_pesaje").sudo()
        pdf, _content_type = report._render_qweb_pdf(
            report.report_name,
            [],
            data={"fecha_planilla": fecha, "campus_id": campus_id},
        )
        headers = [
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf)),
            (
                "Content-Disposition",
                'inline; filename="plantilla_registro_interno_pesaje.pdf"',
            ),
        ]
        return request.make_response(pdf, headers=headers)
