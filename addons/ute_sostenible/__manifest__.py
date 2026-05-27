{
    "name": "UTE Sostenible",
    "summary": "Gestión de puntos ecológicos y registros de pesaje",
    "description": """
UTE Sostenible
===============
Módulo para administrar campus, bloques, pisos, puntos ecológicos, tipos de
residuos y registros de pesaje.

Todo el módulo está nombrado en español a nivel funcional y técnico.
    """,
    "version": "19.0.1.0.0",
    "category": "Sostenibilidad",
    "author": "UTE",
    "license": "LGPL-3",
    "depends": ["base", "mail", "web"],
    "data": [
        "security/seguridad.xml",
        "security/ir.model.access.csv",
        "data/secuencia.xml",
        "data/datos_base.xml",
        "views/plantillas_login.xml",
        "views/vistas_ubicacion.xml",
        "views/vistas_catalogos.xml",
        "views/vistas_puntos_ecologicos.xml",
        "views/vistas_importacion_foto.xml",
        "views/vistas_pesaje.xml",
        "views/vistas_menu.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "ute_sostenible/static/src/scss/estilo_login.scss",
        ],
    },
    "application": True,
    "installable": True,
}
