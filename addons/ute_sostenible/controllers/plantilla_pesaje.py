from odoo import http
from odoo.http import request


class PlantillaPesajeController(http.Controller):
    def _usuario_autorizado(self):
        usuario = request.env.user
        return usuario.has_group("ute_sostenible.grupo_usuario_ute_sostenible") or usuario.has_group(
            "ute_sostenible.grupo_administrador_ute_sostenible"
        )

    @http.route(
        "/ute_sostenible/plantilla_pesaje/pdf",
        type="http",
        auth="user",
    )
    def descargar_plantilla_pesaje(self, fecha=None, campus_id=None, bloque_id=None, **kwargs):
        if not self._usuario_autorizado():
            return request.not_found()

        report = request.env.ref("ute_sostenible.accion_reporte_plantilla_pesaje").sudo()
        pdf, _content_type = report._render_qweb_pdf(
            report.report_name,
            [],
            data={"fecha_planilla": fecha, "campus_id": campus_id, "bloque_id": bloque_id},
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

    @http.route(
        "/ute_sostenible/plantilla_pesaje/xlsx",
        type="http",
        auth="user",
    )
    def descargar_plantilla_pesaje_xlsx(self, fecha=None, campus_id=None, bloque_id=None, **kwargs):
        if not self._usuario_autorizado():
            return request.not_found()

        reporte = request.env["report.ute_sostenible.reporte_plantilla_pesaje"].sudo()
        contenido = reporte._generar_xlsx(fecha=fecha, campus_id=campus_id, bloque_id=bloque_id)
        headers = [
            (
                "Content-Type",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            ("Content-Length", len(contenido)),
            (
                "Content-Disposition",
                'attachment; filename="plantilla_registro_interno_pesaje.xlsx"',
            ),
        ]
        return request.make_response(contenido, headers=headers)
