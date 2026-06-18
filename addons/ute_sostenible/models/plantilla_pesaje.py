from odoo import api, fields, models


class PlantillaPesajeWizard(models.TransientModel):
    _name = "ute_sostenible.plantilla_pesaje_wizard"
    _description = "Asistente para imprimir plantilla de pesaje"

    fecha = fields.Date(
        string="Fecha de la planilla",
        default=fields.Date.context_today,
        required=True,
    )
    campus_id = fields.Many2one(
        "ute_sostenible.campus",
        string="Campus",
        required=True,
        help="Se imprime una planilla con las estaciones de este campus, en orden.",
    )

    def action_imprimir_plantilla(self):
        self.ensure_one()
        fecha = fields.Date.to_string(self.fecha)
        return {
            "type": "ir.actions.act_url",
            "url": f"/ute_sostenible/plantilla_pesaje/pdf?fecha={fecha}&campus_id={self.campus_id.id}",
            "target": "new",
        }


class ReportePlantillaPesaje(models.AbstractModel):
    _name = "report.ute_sostenible.reporte_plantilla_pesaje"
    _description = "Reporte de plantilla de pesaje"

    FILAS_POR_HOJA = 28

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        fecha = data.get("fecha_planilla")
        fecha_texto = ""
        if fecha:
            fecha_obj = fields.Date.from_string(fecha)
            fecha_texto = fecha_obj.strftime("%d/%m/%Y")

        campus = self.env["ute_sostenible.campus"]
        campus_id = data.get("campus_id")
        if campus_id:
            campus = campus.browse(int(campus_id)).exists()

        # Estaciones del campus, en orden edificio → piso → estación
        # (definido en el _order del modelo ute_sostenible.punto_ecologico).
        puntos = self.env["ute_sostenible.punto_ecologico"]
        if campus:
            puntos = puntos.search([("campus_id", "=", campus.id)])
        total = len(puntos)

        # Cada hoja admite como máximo 28 filas porque el escaneo OCR de la
        # planilla numera las filas de 1 a 28 por foto. Si el campus tiene más
        # estaciones se generan varias hojas, cada una renumerada de 1 a 28; las
        # filas que sobran en la última hoja quedan en blanco.
        paginas = []
        for inicio in range(0, max(total, 1), self.FILAS_POR_HOJA):
            grupo = puntos[inicio:inicio + self.FILAS_POR_HOJA]
            filas = []
            for indice in range(self.FILAS_POR_HOJA):
                punto = grupo[indice] if indice < len(grupo) else False
                filas.append(
                    {
                        "numero": indice + 1,
                        "edificio": punto.bloque_id.nombre if punto else "",
                        "piso": punto.piso_id.nombre if punto else "",
                        "estacion": punto.nombre if punto else "",
                    }
                )
            paginas.append(filas)

        return {
            "doc_ids": docids,
            "doc_model": "ute_sostenible.plantilla_pesaje_wizard",
            "docs": self.env["ute_sostenible.plantilla_pesaje_wizard"].browse([]),
            "fecha_planilla_texto": fecha_texto,
            "campus_nombre": campus.nombre or "",
            "paginas": paginas,
            "total_paginas": len(paginas),
            "total_estaciones": total,
        }
