import base64
import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ImportacionFotoPesaje(models.Model):
    _name = "ute_sostenible.importacion_foto_pesaje"
    _description = "Importación de pesaje desde foto"
    _inherit = ["mail.thread", "mail.activity.mixin", "ute_sostenible.importacion_foto_ocr.mixin"]
    _order = "fecha_importacion desc, id desc"

    name = fields.Char(string="Nombre", default="Nueva importación", required=True, tracking=True)
    fecha_importacion = fields.Datetime(
        string="Fecha de importación",
        default=fields.Datetime.now,
        readonly=True,
        tracking=True,
    )
    usuario_importacion_id = fields.Many2one(
        "res.users",
        string="Usuario importador",
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True,
    )
    foto_planilla = fields.Binary(string="Foto de la planilla", attachment=True)
    nombre_archivo = fields.Char(string="Nombre del archivo")
    imagen_procesada = fields.Binary(string="Imagen procesada", attachment=True, readonly=True)
    texto_detectado = fields.Text(string="Texto detectado", readonly=True)
    json_ocr = fields.Text(string="JSON OCR", readonly=True)
    estado = fields.Selection(
        [
            ("borrador", "Borrador"),
            ("procesado", "Procesado"),
            ("confirmado", "Confirmado"),
            ("error", "Error"),
        ],
        string="Estado",
        default="borrador",
        tracking=True,
    )
    mensaje_error = fields.Text(string="Mensaje de error", readonly=True)
    lineas_ids = fields.One2many(
        "ute_sostenible.importacion_foto_pesaje_linea",
        "importacion_id",
        string="Líneas detectadas",
    )
    total_lineas_detectadas = fields.Integer(
        string="Total detectadas",
        compute="_calcular_totales",
    )
    total_lineas_correctas = fields.Integer(
        string="Correctas",
        compute="_calcular_totales",
    )
    total_lineas_revision = fields.Integer(
        string="Por revisar",
        compute="_calcular_totales",
    )
    total_lineas_error = fields.Integer(
        string="Con error",
        compute="_calcular_totales",
    )

    @api.depends("lineas_ids.estado_linea")
    def _calcular_totales(self):
        for registro in self:
            lineas = registro.lineas_ids
            registro.total_lineas_detectadas = len(lineas)
            registro.total_lineas_correctas = len(lineas.filtered(lambda linea: linea.estado_linea == "correcto"))
            registro.total_lineas_revision = len(lineas.filtered(lambda linea: linea.estado_linea == "revisar"))
            registro.total_lineas_error = len(lineas.filtered(lambda linea: linea.estado_linea == "error"))

    def action_procesar_foto(self):
        for registro in self:
            if not registro.foto_planilla:
                raise UserError(_("Debe subir o tomar una foto de la planilla."))
            try:
                imagen_bytes = registro._decodificar_imagen()
                procesada_bytes, metadatos_imagen = registro._preprocesar_imagen(imagen_bytes)
                imagen_para_ocr = procesada_bytes or imagen_bytes
                texto, metadatos_ocr = registro._extraer_texto_ocr(imagen_para_ocr)
                filas_celdas, metadatos_tabla = registro._extraer_tabla_por_celdas(imagen_para_ocr)
                filas = filas_celdas or registro._detectar_filas_tabla(texto)
                valores = {
                    "imagen_procesada": base64.b64encode(procesada_bytes).decode() if procesada_bytes else False,
                    "texto_detectado": texto,
                    "json_ocr": json.dumps(
                        {
                            "imagen": metadatos_imagen,
                            "ocr": metadatos_ocr,
                            "tabla": metadatos_tabla,
                            "filas_detectadas": filas,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    "mensaje_error": False,
                }
                registro.lineas_ids.unlink()
                if not metadatos_ocr.get("disponible"):
                    valores.update(
                        {
                            "estado": "procesado",
                            "mensaje_error": _(
                                "OCR no disponible. Puede ingresar las líneas manualmente en la tabla."
                            ),
                        }
                    )
                    registro.write(valores)
                    registro._crear_lineas_manuales()
                    continue
                if not filas:
                    valores.update(
                        {
                            "estado": "procesado",
                            "mensaje_error": _(
                                "No se detectaron filas claras. Puede ingresar o corregir las líneas manualmente."
                            ),
                        }
                    )
                    registro.write(valores)
                    registro._crear_lineas_manuales()
                    continue
                registro.write({**valores, "estado": "procesado"})
                registro._crear_lineas_desde_filas(filas)
            except Exception as exc:
                _logger.exception("Error al procesar foto de pesaje")
                registro.write({"estado": "error", "mensaje_error": str(exc)})
        return True

    def action_recalcular_lineas(self):
        for registro in self:
            for linea in registro.lineas_ids:
                linea._autocompletar_y_clasificar()
        return True

    def action_crear_registros(self):
        Registro = self.env["ute_sostenible.registro_pesaje"].sudo()
        total_creados = total_revision = total_error = 0
        for importacion in self:
            for linea in importacion.lineas_ids.filtered("crear_registro"):
                linea._autocompletar_y_clasificar()
                if linea.estado_linea == "error":
                    total_error += 1
                    continue
                if not linea.punto_ecologico_id:
                    linea.write(
                        {
                            "estado_linea": "error",
                            "mensaje_error": linea._agregar_mensaje(
                                linea.mensaje_error,
                                "No se puede crear el registro sin Estación / Punto ecológico.",
                            ),
                        }
                    )
                    total_error += 1
                    continue
                try:
                    registro_pesaje = Registro.create(linea._preparar_valores_registro())
                    linea._publicar_foto_en_chatter(registro_pesaje)
                    linea.write({"crear_registro": False, "mensaje_error": False})
                    total_creados += 1
                except Exception as exc:
                    _logger.exception("Error al crear registro desde línea OCR")
                    linea.write(
                        {
                            "estado_linea": "error",
                            "mensaje_error": linea._agregar_mensaje(linea.mensaje_error, str(exc)),
                        }
                    )
                    total_error += 1
            total_revision += len(importacion.lineas_ids.filtered(lambda linea: linea.estado_linea == "revisar"))
            if total_creados:
                importacion.estado = "confirmado"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Importación desde foto"),
                "message": _(
                    "Se crearon %(creados)s registros. %(revision)s líneas requieren revisión. %(error)s líneas tienen error.",
                    creados=total_creados,
                    revision=total_revision,
                    error=total_error,
                ),
                "type": "success" if total_creados else "warning",
                "sticky": False,
            },
        }
