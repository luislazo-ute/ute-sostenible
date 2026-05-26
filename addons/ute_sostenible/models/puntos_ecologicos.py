from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PuntoEcologico(models.Model):
    _name = "ute_sostenible.punto_ecologico"
    _description = "Punto ecológico"
    _inherit = ["ute_sostenible.modelo_base"]
    _order = "campus_id, bloque_id, piso_id, nombre"

    campus_id = fields.Many2one(
        "ute_sostenible.campus",
        string="Campus",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    bloque_id = fields.Many2one(
        "ute_sostenible.bloque",
        string="Bloque / Edificio",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    piso_id = fields.Many2one(
        "ute_sostenible.piso",
        string="Piso",
        ondelete="restrict",
        tracking=True,
    )
    categoria_id = fields.Many2one(
        "ute_sostenible.categoria",
        string="Categoría",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    tipo_contenedor_id = fields.Many2one(
        "ute_sostenible.tipo_contenedor",
        string="Tipo de contenedor",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    cantidad_planificada = fields.Integer(string="Cantidad planificada", default=1, tracking=True)
    cantidad_instalada = fields.Integer(string="Cantidad instalada", default=0, tracking=True)
    costo_estimado = fields.Monetary(
        string="Costo estimado",
        compute="_calcular_costo_estimado",
        currency_field="moneda_id",
        store=True,
    )
    moneda_id = fields.Many2one(
        related="tipo_contenedor_id.moneda_id",
        string="Moneda",
        store=True,
        readonly=True,
    )
    responsable_id = fields.Many2one(
        "res.users",
        string="Responsable",
        default=lambda self: self.env.user,
        tracking=True,
    )
    estado = fields.Selection(
        [
            ("planificado", "Planificado"),
            ("instalado", "Instalado"),
            ("inactivo", "Inactivo"),
        ],
        string="Estado",
        default="planificado",
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for valores in vals_list:
            if not valores.get("codigo") or valores.get("codigo") == "Nuevo":
                valores["codigo"] = self._generar_codigo_unico("ute_sostenible.punto_ecologico")
        return super().create(vals_list)

    @api.depends("cantidad_planificada", "tipo_contenedor_id.costo_total")
    def _calcular_costo_estimado(self):
        for registro in self:
            registro.costo_estimado = (registro.cantidad_planificada or 0) * (
                registro.tipo_contenedor_id.costo_total or 0.0
            )

    @api.onchange("bloque_id")
    def _onchange_bloque_id(self):
        for registro in self:
            if registro.bloque_id:
                registro.campus_id = registro.bloque_id.campus_id
                if registro.piso_id and registro.piso_id.bloque_id != registro.bloque_id:
                    registro.piso_id = False

    @api.constrains("cantidad_planificada", "cantidad_instalada")
    def _validar_cantidades(self):
        for registro in self:
            if registro.cantidad_planificada < 0 or registro.cantidad_instalada < 0:
                raise ValidationError("Las cantidades no pueden ser negativas.")

    _punto_ecologico_codigo_unico = models.Constraint(
        "unique(codigo)",
        "Ya existe un punto ecológico con ese código.",
    )

    def accion_marcar_instalado(self):
        for registro in self:
            registro.cantidad_instalada = registro.cantidad_planificada
            registro.estado = "instalado"

    def accion_marcar_planificado(self):
        self.write({"estado": "planificado"})

    def accion_marcar_inactivo(self):
        self.write({"estado": "inactivo"})
