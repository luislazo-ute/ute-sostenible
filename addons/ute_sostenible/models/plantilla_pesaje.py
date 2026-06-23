import io

from markupsafe import Markup, escape

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
    bloque_id = fields.Many2one(
        "ute_sostenible.bloque",
        string="Bloque / Edificio (opcional)",
        help="Si se elige un bloque, la planilla sale solo de ese bloque. "
        "Si se deja vacío, salen todas las estaciones del campus.",
    )

    @api.onchange("campus_id")
    def _onchange_campus_id(self):
        # Al cambiar de campus se limpia el bloque para no dejar uno de otro campus.
        if self.bloque_id and self.bloque_id.campus_id != self.campus_id:
            self.bloque_id = False

    def _url_descarga(self, formato):
        """Construye la URL de descarga (pdf o xlsx) con los filtros elegidos."""
        self.ensure_one()
        fecha = fields.Date.to_string(self.fecha)
        url = f"/ute_sostenible/plantilla_pesaje/{formato}?fecha={fecha}&campus_id={self.campus_id.id}"
        if self.bloque_id:
            url += f"&bloque_id={self.bloque_id.id}"
        return url

    def action_imprimir_plantilla(self):
        return {
            "type": "ir.actions.act_url",
            "url": self._url_descarga("pdf"),
            "target": "new",
        }

    def action_exportar_excel(self):
        return {
            "type": "ir.actions.act_url",
            "url": self._url_descarga("xlsx"),
            "target": "new",
        }


class ReportePlantillaPesaje(models.AbstractModel):
    _name = "report.ute_sostenible.reporte_plantilla_pesaje"
    _description = "Reporte de plantilla de pesaje"

    FILAS_POR_HOJA = 28

    @api.model
    def _texto_html(self, valor):
        """Devuelve el texto seguro para HTML con los caracteres no ASCII
        convertidos a entidades numericas (por ejemplo 'í' -> '&#237;').

        Las entidades numericas se renderizan igual sin importar la
        codificacion que reciba wkhtmltopdf, asi que las tildes y la 'ñ'
        salen bien en el PDF aunque al motor no le llegue el charset UTF-8.
        """
        if not valor:
            return ""
        escapado = str(escape(valor))
        return Markup(
            "".join(caracter if ord(caracter) < 128 else f"&#{ord(caracter)};" for caracter in escapado)
        )

    @api.model
    def _obtener_puntos(self, campus_id=None, bloque_id=None):
        """Estaciones (puntos ecológicos) del campus —y bloque, si se indica—
        en orden edificio → piso → estación (definido en el _order del modelo
        ute_sostenible.punto_ecologico). Sin campus devuelve recordset vacío."""
        if not campus_id:
            return self.env["ute_sostenible.punto_ecologico"].browse([])
        dominio = [("campus_id", "=", int(campus_id))]
        if bloque_id:
            dominio.append(("bloque_id", "=", int(bloque_id)))
        return self.env["ute_sostenible.punto_ecologico"].search(dominio)

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
        bloque = self.env["ute_sostenible.bloque"]
        bloque_id = data.get("bloque_id")
        if bloque_id:
            bloque = bloque.browse(int(bloque_id)).exists()

        puntos = self._obtener_puntos(campus_id, bloque_id)
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
                        "edificio": self._texto_html(punto.bloque_id.nombre) if punto else "",
                        "piso": self._texto_html(punto.piso_id.nombre) if punto else "",
                        "estacion": self._texto_html(punto.nombre) if punto else "",
                    }
                )
            paginas.append(filas)

        return {
            "doc_ids": docids,
            "doc_model": "ute_sostenible.plantilla_pesaje_wizard",
            "docs": self.env["ute_sostenible.plantilla_pesaje_wizard"].browse([]),
            "fecha_planilla_texto": fecha_texto,
            "campus_nombre": self._texto_html(campus.nombre),
            "bloque_nombre": self._texto_html(bloque.nombre),
            "paginas": paginas,
            "total_paginas": len(paginas),
            "total_estaciones": total,
        }

    @api.model
    def _generar_xlsx(self, fecha=None, campus_id=None, bloque_id=None):
        """Genera la planilla en Excel (.xlsx) con las mismas columnas que el
        PDF. Lista todas las estaciones del campus/bloque en una sola hoja
        (el Excel no se escanea por OCR, así que no aplica el tope de 28)."""
        import xlsxwriter

        fecha_texto = ""
        if fecha:
            fecha_texto = fields.Date.from_string(fecha).strftime("%d/%m/%Y")
        campus = self.env["ute_sostenible.campus"]
        if campus_id:
            campus = campus.browse(int(campus_id)).exists()
        bloque = self.env["ute_sostenible.bloque"]
        if bloque_id:
            bloque = bloque.browse(int(bloque_id)).exists()
        puntos = self._obtener_puntos(campus_id, bloque_id)

        salida = io.BytesIO()
        libro = xlsxwriter.Workbook(salida, {"in_memory": True})
        hoja = libro.add_worksheet("Pesaje")
        hoja.set_landscape()

        f_titulo = libro.add_format({"bold": True, "font_size": 14, "align": "center", "valign": "vcenter"})
        f_sub = libro.add_format({"font_size": 11, "align": "center", "valign": "vcenter"})
        f_cab = libro.add_format(
            {"bold": True, "bg_color": "#F3F4F6", "border": 1, "align": "center", "valign": "vcenter", "text_wrap": True}
        )
        f_texto = libro.add_format({"border": 1, "valign": "vcenter"})
        f_centro = libro.add_format({"border": 1, "align": "center", "valign": "vcenter"})

        columnas = [
            ("No.", 5),
            ("Fecha", 12),
            ("Hora", 8),
            ("Responsable", 20),
            ("Edificio", 20),
            ("Piso", 12),
            ("Estación", 40),
            ("Bolsa azul (kg)", 12),
            ("Bolsa negra (kg)", 12),
            ("Bolsa verde (kg)", 12),
            ("Observaciones", 26),
            ("Firma", 18),
        ]
        for indice, (_titulo, ancho) in enumerate(columnas):
            hoja.set_column(indice, indice, ancho)

        ultima_col = len(columnas) - 1
        hoja.merge_range(0, 0, 0, ultima_col, "Registro interno de pesaje", f_titulo)
        ubicacion = "Campus: %s" % (campus.nombre or "")
        if bloque:
            ubicacion += "   -   Edificio: %s" % bloque.nombre
        hoja.merge_range(1, 0, 1, ultima_col, ubicacion, f_sub)
        hoja.merge_range(2, 0, 2, ultima_col, "Fecha: %s" % (fecha_texto or ""), f_sub)

        fila_cabecera = 4
        for col, (titulo, _ancho) in enumerate(columnas):
            hoja.write(fila_cabecera, col, titulo, f_cab)

        fila = fila_cabecera + 1
        for indice, punto in enumerate(puntos, start=1):
            hoja.write_number(fila, 0, indice, f_centro)
            hoja.write(fila, 1, fecha_texto or "", f_centro)
            hoja.write(fila, 2, "", f_centro)
            hoja.write(fila, 3, "", f_texto)
            hoja.write(fila, 4, punto.bloque_id.nombre or "", f_texto)
            hoja.write(fila, 5, punto.piso_id.nombre or "", f_centro)
            hoja.write(fila, 6, punto.nombre or "", f_texto)
            hoja.write(fila, 7, "", f_centro)
            hoja.write(fila, 8, "", f_centro)
            hoja.write(fila, 9, "", f_centro)
            hoja.write(fila, 10, "", f_texto)
            hoja.write(fila, 11, "", f_texto)
            fila += 1

        libro.close()
        return salida.getvalue()
