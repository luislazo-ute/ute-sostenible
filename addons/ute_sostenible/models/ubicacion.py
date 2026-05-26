from odoo import api, fields, models


class Campus(models.Model):
    _name = "ute_sostenible.campus"
    _description = "Campus"
    _inherit = ["ute_sostenible.modelo_base"]
    _order = "nombre"

    bloque_ids = fields.One2many(
        "ute_sostenible.bloque",
        "campus_id",
        string="Bloques",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for valores in vals_list:
            if not valores.get("codigo") or valores.get("codigo") == "Nuevo":
                valores["codigo"] = self._generar_codigo_unico("ute_sostenible.campus")
        return super().create(vals_list)

    _campus_nombre_unico = models.Constraint(
        "unique(nombre)",
        "Ya existe un campus con ese nombre.",
    )
    _campus_codigo_unico = models.Constraint(
        "unique(codigo)",
        "Ya existe un campus con ese código.",
    )


class Bloque(models.Model):
    _name = "ute_sostenible.bloque"
    _description = "Bloque o edificio"
    _inherit = ["ute_sostenible.modelo_base"]
    _order = "campus_id, nombre"

    campus_id = fields.Many2one(
        "ute_sostenible.campus",
        string="Campus",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    piso_ids = fields.One2many(
        "ute_sostenible.piso",
        "bloque_id",
        string="Pisos",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for valores in vals_list:
            if not valores.get("codigo") or valores.get("codigo") == "Nuevo":
                valores["codigo"] = self._generar_codigo_unico("ute_sostenible.bloque")
        return super().create(vals_list)

    _bloque_unico_por_campus = models.Constraint(
        "unique(nombre, campus_id)",
        "El bloque o edificio ya existe en este campus.",
    )
    _bloque_codigo_unico = models.Constraint(
        "unique(codigo)",
        "Ya existe un bloque o edificio con ese código.",
    )


class Piso(models.Model):
    _name = "ute_sostenible.piso"
    _description = "Piso"
    _inherit = ["ute_sostenible.modelo_base"]
    _order = "bloque_id, secuencia, nombre"

    secuencia = fields.Integer(
        string="Orden",
        default=10,
        help="Campo técnico para ordenar los pisos en listas y selecciones.",
    )
    bloque_id = fields.Many2one(
        "ute_sostenible.bloque",
        string="Bloque / Edificio",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    campus_id = fields.Many2one(
        related="bloque_id.campus_id",
        string="Campus",
        store=True,
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for valores in vals_list:
            if not valores.get("codigo") or valores.get("codigo") == "Nuevo":
                valores["codigo"] = self._generar_codigo_unico("ute_sostenible.piso")
        return super().create(vals_list)

    _piso_unico_por_bloque = models.Constraint(
        "unique(nombre, bloque_id)",
        "El piso ya existe en este bloque o edificio.",
    )
    _piso_codigo_unico = models.Constraint(
        "unique(codigo)",
        "Ya existe un piso con ese código.",
    )
