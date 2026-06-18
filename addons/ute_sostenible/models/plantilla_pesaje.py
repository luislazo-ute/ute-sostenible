from odoo import api, fields, models


class PlantillaPesajeWizard(models.TransientModel):
    _name = "ute_sostenible.plantilla_pesaje_wizard"
    _description = "Asistente para imprimir plantilla de pesaje"

    fecha = fields.Date(
        string="Fecha de la planilla",
        default=fields.Date.context_today,
        required=True,
    )

    def action_imprimir_plantilla(self):
        self.ensure_one()
        fecha = fields.Date.to_string(self.fecha)
        return {
            "type": "ir.actions.act_url",
            "url": f"/ute_sostenible/plantilla_pesaje/pdf?fecha={fecha}",
            "target": "new",
        }


class ReportePlantillaPesaje(models.AbstractModel):
    _name = "report.ute_sostenible.reporte_plantilla_pesaje"
    _description = "Reporte de plantilla de pesaje"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        fecha = data.get("fecha_planilla")
        fecha_texto = ""
        if fecha:
            fecha_obj = fields.Date.from_string(fecha)
            fecha_texto = fecha_obj.strftime("%d/%m/%Y")
        return {
            "doc_ids": docids,
            "doc_model": "ute_sostenible.plantilla_pesaje_wizard",
            "docs": self.env["ute_sostenible.plantilla_pesaje_wizard"].browse([]),
            "fecha_planilla_texto": fecha_texto,
        }
