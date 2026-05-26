from odoo import api, fields, models


class Categoria(models.Model):
    _name = "ute_sostenible.categoria"
    _description = "Categoría"
    _inherit = ["ute_sostenible.modelo_base"]
    _order = "nombre"

    @api.model_create_multi
    def create(self, vals_list):
        for valores in vals_list:
            if not valores.get("codigo") or valores.get("codigo") == "Nuevo":
                valores["codigo"] = self._generar_codigo_unico("ute_sostenible.categoria")
        return super().create(vals_list)

    _categoria_nombre_unico = models.Constraint(
        "unique(nombre)",
        "Ya existe una categoría con ese nombre.",
    )


class TipoContenedor(models.Model):
    _name = "ute_sostenible.tipo_contenedor"
    _description = "Tipo de contenedor"
    _inherit = ["ute_sostenible.modelo_base"]
    _order = "nombre"

    capacidad_litros = fields.Float(string="Capacidad (litros)")
    numero_contenedores = fields.Integer(string="Número de contenedores", default=1)
    es_reutilizado = fields.Boolean(string="Es reutilizado")
    color_senaletica = fields.Char(string="Color / Señalética")
    costo_unitario = fields.Monetary(
        string="Costo unitario",
        currency_field="moneda_id",
    )
    iva_porcentaje = fields.Float(string="IVA (%)", default=15.0)
    costo_total = fields.Monetary(
        string="Costo total con IVA",
        compute="_calcular_costo_total",
        currency_field="moneda_id",
        store=True,
    )
    moneda_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    @api.depends("costo_unitario", "iva_porcentaje")
    def _calcular_costo_total(self):
        for registro in self:
            iva = (registro.iva_porcentaje or 0.0) / 100.0
            registro.costo_total = (registro.costo_unitario or 0.0) * (1 + iva)

    @api.model_create_multi
    def create(self, vals_list):
        for valores in vals_list:
            if not valores.get("codigo") or valores.get("codigo") == "Nuevo":
                valores["codigo"] = self._generar_codigo_unico("ute_sostenible.tipo_contenedor")
        return super().create(vals_list)


class TipoResiduo(models.Model):
    _name = "ute_sostenible.tipo_residuo"
    _description = "Tipo de residuo"
    _inherit = ["ute_sostenible.modelo_base"]
    _order = "secuencia, nombre"

    secuencia = fields.Integer(string="Secuencia", default=10)
    color_bolsa = fields.Selection(
        [
            ("azul", "Bolsa azul"),
            ("negra", "Bolsa negra"),
            ("verde", "Bolsa verde"),
            ("otra", "Otra"),
        ],
        string="Color de bolsa",
        default="otra",
    )

    _tipo_residuo_nombre_unico = models.Constraint(
        "unique(nombre)",
        "Ya existe un tipo de residuo con ese nombre.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for valores in vals_list:
            if not valores.get("codigo") or valores.get("codigo") == "Nuevo":
                valores["codigo"] = self._generar_codigo_unico("ute_sostenible.tipo_residuo")
        return super().create(vals_list)
