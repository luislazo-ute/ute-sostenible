from odoo import _, api, fields, models


class ImportacionFotoPesajeLinea(models.Model):
    _name = "ute_sostenible.importacion_foto_pesaje_linea"
    _description = "Línea de importación de pesaje desde foto"
    _order = "importacion_id, numero_linea, id"

    importacion_id = fields.Many2one(
        "ute_sostenible.importacion_foto_pesaje",
        string="Importación",
        required=True,
        ondelete="cascade",
    )
    numero_linea = fields.Integer(string="N°")
    fecha = fields.Date(string="Fecha")
    hora = fields.Float(string="Hora")
    responsable_texto = fields.Char(string="Responsable detectado")
    responsable_id = fields.Many2one("res.users", string="Responsable")
    edificio_texto = fields.Char(string="Edificio detectado")
    bloque_id = fields.Many2one("ute_sostenible.bloque", string="Edificio")
    piso_texto = fields.Char(string="Piso detectado")
    piso_id = fields.Many2one("ute_sostenible.piso", string="Piso")
    estacion = fields.Char(string="Estación")
    punto_ecologico_id = fields.Many2one("ute_sostenible.punto_ecologico", string="Estación / Punto ecológico")
    bolsa_azul = fields.Float(string="Bolsa azul")
    bolsa_negra = fields.Float(string="Bolsa negra")
    bolsa_verde = fields.Float(string="Bolsa verde")
    observaciones = fields.Char(string="Observaciones")
    firma_texto = fields.Char(string="Firma detectada")
    crear_registro = fields.Boolean(string="Crear registro", default=True)
    estado_linea = fields.Selection(
        [
            ("correcto", "Correcto"),
            ("revisar", "Revisar"),
            ("error", "Error"),
        ],
        string="Estado",
        default="revisar",
    )
    confianza_ocr = fields.Float(string="Confianza OCR")
    mensaje_error = fields.Text(string="Mensaje")
    texto_original_linea = fields.Text(string="Texto original")

    @api.onchange(
        "fecha",
        "hora",
        "responsable_texto",
        "edificio_texto",
        "bloque_id",
        "piso_texto",
        "piso_id",
        "estacion",
        "punto_ecologico_id",
        "bolsa_azul",
        "bolsa_negra",
        "bolsa_verde",
    )
    def _onchange_clasificar(self):
        for linea in self:
            linea._autocompletar_y_clasificar()

    def _autocompletar_y_clasificar(self):
        for linea in self:
            helper = linea.importacion_id
            if not linea.responsable_id and linea.responsable_texto:
                linea.responsable_id = helper._buscar_responsable(linea.responsable_texto)
            if not linea.bloque_id and linea.edificio_texto:
                linea.bloque_id = helper._buscar_bloque(linea.edificio_texto)
            if not linea.piso_id and linea.piso_texto:
                linea.piso_id = helper._buscar_piso(linea.piso_texto, linea.bloque_id)
            if not linea.punto_ecologico_id:
                linea.punto_ecologico_id = helper._buscar_punto_ecologico(
                    linea.estacion,
                    linea.bloque_id,
                    linea.piso_id,
                )
            estado, mensaje = linea._clasificar_estado_linea()
            linea.estado_linea = estado
            linea.mensaje_error = mensaje
            linea.crear_registro = estado != "error"

    def _clasificar_estado_linea(self):
        self.ensure_one()
        mensajes = []
        peso_total = (self.bolsa_azul or 0.0) + (self.bolsa_negra or 0.0) + (self.bolsa_verde or 0.0)
        ubicacion_minima = bool(self.bloque_id or self.edificio_texto or self.estacion or self.punto_ecologico_id)
        if not any(
            [
                self.fecha,
                self.responsable_texto,
                self.edificio_texto,
                self.piso_texto,
                self.estacion,
                peso_total,
                self.observaciones,
            ]
        ):
            return "error", "Línea vacía."
        if not self.fecha:
            mensajes.append("Falta fecha válida.")
        if not ubicacion_minima:
            mensajes.append("Falta ubicación mínima.")
        if peso_total <= 0:
            mensajes.append("No hay peso válido en bolsa azul, negra o verde.")
        if mensajes:
            return "error", " ".join(mensajes)
        if not self.responsable_id:
            mensajes.append("Responsable no encontrado.")
        if not self.piso_id:
            mensajes.append("Piso no encontrado.")
        if not self.punto_ecologico_id:
            mensajes.append("Punto ecológico no encontrado.")
        if self.confianza_ocr and self.confianza_ocr < 0.5:
            mensajes.append("Confianza OCR baja.")
        if mensajes:
            return "revisar", " ".join(mensajes)
        return "correcto", False

    def _preparar_valores_registro(self):
        self.ensure_one()
        tipos = self._obtener_tipos_residuo()
        lineas = []
        for clave, peso in [
            ("azul", self.bolsa_azul),
            ("negra", self.bolsa_negra),
            ("verde", self.bolsa_verde),
        ]:
            tipo = tipos.get(clave)
            if tipo:
                lineas.append(
                    (
                        0,
                        0,
                        {
                            "tipo_residuo_id": tipo.id,
                            "presente": bool(peso and peso > 0),
                            "peso_kg": peso or 0.0,
                            "observaciones": self.observaciones,
                        },
                    )
                )
        return {
            "fecha": self.fecha,
            "hora": self.hora or 0.0,
            "responsable_id": self.responsable_id.id or self.env.user.id,
            "origen": "interno",
            "origen_registro": "importacion_foto",
            "punto_ecologico_id": self.punto_ecologico_id.id,
            "linea_ids": lineas,
            "observaciones": self.observaciones,
            "firma": self.firma_texto,
            "foto_planilla_origen": self.importacion_id.foto_planilla,
            "numero_linea_importada": self.numero_linea,
            "texto_origen_importacion": self.texto_original_linea,
            "importacion_foto_nombre": self.importacion_id.name,
        }

    def _publicar_foto_en_chatter(self, registro_pesaje):
        self.ensure_one()
        if not self.importacion_id.foto_planilla:
            return
        nombre_archivo = self.importacion_id.nombre_archivo or f"{self.importacion_id.name}.png"
        adjunto = self.env["ir.attachment"].sudo().create(
            {
                "name": nombre_archivo,
                "type": "binary",
                "datas": self.importacion_id.foto_planilla,
                "res_model": registro_pesaje._name,
                "res_id": registro_pesaje.id,
            }
        )
        registro_pesaje.message_post(
            body=_(
                "Registro creado desde importación por foto %(importacion)s, línea %(linea)s.",
                importacion=self.importacion_id.name,
                linea=self.numero_linea or "",
            ),
            attachment_ids=[adjunto.id],
        )

    def _obtener_tipos_residuo(self):
        Tipo = self.env["ute_sostenible.tipo_residuo"].sudo()
        tipos = {}
        for color, nombres in {
            "azul": ["Reciclable"],
            "negra": ["No reciclable"],
            "verde": ["Orgánico", "Organico"],
        }.items():
            tipo = Tipo.search([("color_bolsa", "=", color)], limit=1)
            if not tipo:
                tipo = Tipo.search([("nombre", "in", nombres)], limit=1)
            if tipo:
                tipos[color] = tipo
        return tipos

    def _agregar_mensaje(self, mensaje_actual, nuevo_mensaje):
        mensajes = [mensaje for mensaje in [mensaje_actual, nuevo_mensaje] if mensaje]
        return " ".join(mensajes)
