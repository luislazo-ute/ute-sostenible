from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RegistroPesaje(models.Model):
    _name = "ute_sostenible.registro_pesaje"
    _description = "Registro de pesaje"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "numero"
    _order = "fecha desc, id desc"

    numero = fields.Char(string="N°", default="Nuevo", copy=False, readonly=True)
    fecha = fields.Date(string="Fecha", default=fields.Date.context_today, required=True, tracking=True)
    hora = fields.Float(string="Hora", help="Formato 24h. Ejemplo: 13:30", tracking=True)
    responsable_id = fields.Many2one(
        "res.users",
        string="Responsable",
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
    )
    origen = fields.Selection(
        [
            ("interno", "Registro interno"),
            ("obrero", "Planilla peso obrero"),
            ("servicio_reciclaje", "Planilla servicio de reciclaje"),
        ],
        string="Origen",
        default="interno",
        required=True,
        tracking=True,
    )
    punto_ecologico_id = fields.Many2one(
        "ute_sostenible.punto_ecologico",
        string="Estación / Punto ecológico",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    campus_id = fields.Many2one(
        related="punto_ecologico_id.campus_id",
        string="Campus",
        store=True,
        readonly=True,
    )
    bloque_id = fields.Many2one(
        related="punto_ecologico_id.bloque_id",
        string="Edificio",
        store=True,
        readonly=True,
    )
    piso_id = fields.Many2one(
        related="punto_ecologico_id.piso_id",
        string="Piso",
        store=True,
        readonly=True,
    )
    linea_ids = fields.One2many(
        "ute_sostenible.linea_registro_pesaje",
        "registro_id",
        string="Tipos de residuo",
    )
    peso_total_kg = fields.Float(string="Total kg", compute="_calcular_peso_total", store=True)
    observaciones = fields.Text(string="Observaciones")
    firma = fields.Char(string="Firma / Recibido por")
    estado = fields.Selection(
        [
            ("borrador", "Borrador"),
            ("confirmado", "Confirmado"),
            ("cancelado", "Cancelado"),
        ],
        string="Estado",
        default="borrador",
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for valores in vals_list:
            if not valores.get("numero") or valores.get("numero") == "Nuevo":
                valores["numero"] = self._generar_numero_unico() or "Nuevo"
        return super().create(vals_list)

    def _generar_numero_unico(self):
        numero = self.env["ir.sequence"].next_by_code("ute_sostenible.registro_pesaje")
        while numero and self.search_count([("numero", "=", numero)]):
            numero = self.env["ir.sequence"].next_by_code("ute_sostenible.registro_pesaje")
        return numero

    @api.model
    def default_get(self, campos):
        resultado = super().default_get(campos)
        if "linea_ids" in campos and not resultado.get("linea_ids"):
            tipos_residuo = self.env["ute_sostenible.tipo_residuo"].search([])
            resultado["linea_ids"] = [
                (0, 0, {"tipo_residuo_id": tipo_residuo.id}) for tipo_residuo in tipos_residuo
            ]
        return resultado

    @api.depends("linea_ids.peso_kg")
    def _calcular_peso_total(self):
        for registro in self:
            registro.peso_total_kg = sum(registro.linea_ids.mapped("peso_kg"))

    @api.constrains("linea_ids")
    def _validar_pesos(self):
        for registro in self:
            for linea in registro.linea_ids:
                if linea.peso_kg < 0:
                    raise ValidationError("El peso no puede ser negativo.")

    def accion_confirmar(self):
        self.write({"estado": "confirmado"})

    def accion_cancelar(self):
        self.write({"estado": "cancelado"})

    def accion_volver_borrador(self):
        self.write({"estado": "borrador"})

    _numero_unico = models.Constraint(
        "unique(numero)",
        "Ya existe un registro de pesaje con ese número.",
    )


class LineaRegistroPesaje(models.Model):
    _name = "ute_sostenible.linea_registro_pesaje"
    _description = "Línea de registro de pesaje"
    _order = "registro_id, tipo_residuo_id"

    registro_id = fields.Many2one(
        "ute_sostenible.registro_pesaje",
        string="Registro",
        required=True,
        ondelete="cascade",
    )
    tipo_residuo_id = fields.Many2one(
        "ute_sostenible.tipo_residuo",
        string="Tipo de residuo",
        required=True,
        ondelete="restrict",
    )
    presente = fields.Boolean(string="X / Presente", default=True)
    peso_kg = fields.Float(string="Peso kg")
    observaciones = fields.Char(string="Observación")

    _tipo_residuo_unico_por_registro = models.Constraint(
        "unique(registro_id, tipo_residuo_id)",
        "El tipo de residuo ya está registrado en este pesaje.",
    )
