from odoo import fields, models


class ModeloBaseUteSostenible(models.AbstractModel):
    _name = "ute_sostenible.modelo_base"
    _description = "Herencia base UTE Sostenible"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "nombre"
    _order = "nombre"

    nombre = fields.Char(string="Nombre", required=True, tracking=True)
    codigo = fields.Char(string="Código", tracking=True)
    descripcion = fields.Text(string="Descripción")
    activo = fields.Boolean(string="Activo", default=True, tracking=True)
    color_indicador = fields.Integer(string="Color")

    def _generar_codigo_unico(self, codigo_secuencia):
        codigo = self.env["ir.sequence"].next_by_code(codigo_secuencia)
        while codigo and self.search_count([("codigo", "=", codigo)]):
            codigo = self.env["ir.sequence"].next_by_code(codigo_secuencia)
        return codigo
