# Instalacion en Odoo 19

Esta guia explica como instalar el modulo **UTE Sostenible** en una instalacion normal de Odoo 19 Community, sin Docker.

## Requisitos

- Odoo 19 Community instalado y funcionando.
- PostgreSQL configurado para Odoo.
- Acceso al servidor donde esta instalado Odoo.
- Permisos para copiar modulos personalizados.
- Dependencias base de Odoo disponibles: `base`, `mail` y `web`.

## Ubicacion del modulo

El modulo tecnico se llama:

```text
ute_sostenible
```

Debe copiarse en una ruta incluida en `addons_path`. Por ejemplo:

```text
C:\odoo-custom-addons\ute_sostenible
```

La estructura esperada es:

```text
custom-addons/
└── ute_sostenible/
    ├── __manifest__.py
    ├── models/
    ├── security/
    ├── views/
    ├── data/
    └── static/
```

## Configurar addons_path

Editar el archivo de configuracion de Odoo, por ejemplo:

```text
C:\Program Files\Odoo 19.0\server\odoo.conf
```

Agregar la ruta de modulos personalizados:

```ini
addons_path = C:\Program Files\Odoo 19.0\server\odoo\addons,C:\odoo-custom-addons
```

Guardar los cambios y reiniciar Odoo:

```powershell
Restart-Service -Name "odoo-server-19.0"
```

Si el servicio tiene otro nombre, revisarlo con:

```powershell
Get-Service *odoo*
```

## Actualizar lista de aplicaciones

Entrar a Odoo con un usuario administrador y activar modo desarrollador.

Luego ir a:

```text
Aplicaciones -> Actualizar lista de aplicaciones
```

Buscar:

```text
UTE Sostenible
```

Instalar el modulo.

## Actualizar el modulo despues de cambios

Si se realizan cambios en Python, XML, seguridad o datos, reiniciar Odoo y actualizar el modulo:

```powershell
Restart-Service -Name "odoo-server-19.0"
```

Desde la interfaz:

```text
Aplicaciones -> UTE Sostenible -> Actualizar
```

Tambien se puede actualizar por consola:

```powershell
cd "C:\Program Files\Odoo 19.0\server"
.\odoo-bin -d nombre_base_datos -u ute_sostenible --stop-after-init
```

## Funcionalidad incluida

El modulo permite administrar:

- Campus.
- Bloques / Edificios.
- Pisos.
- Categorias.
- Tipos de contenedor.
- Puntos ecologicos.
- Tipos de residuo.
- Registros de pesaje.
- Lineas de registro de pesaje.

## Roles de seguridad

El modulo crea dos grupos:

- Usuario UTE Sostenible.
- Administrador UTE Sostenible.

El administrador puede gestionar catalogos, puntos ecologicos y registros. El usuario puede consultar catalogos y registrar pesajes segun las reglas configuradas.

## Verificacion tecnica

Antes de instalar o actualizar, se recomienda validar:

```powershell
py -3 -m compileall C:\odoo-custom-addons\ute_sostenible
```

Si se tiene `xmllint` instalado:

```powershell
Get-ChildItem C:\odoo-custom-addons\ute_sostenible -Recurse -Filter *.xml | ForEach-Object {
    xmllint --noout $_.FullName
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
```

Si aparece un error de vistas, permisos o modelos, revisar primero:

```text
security/ir.model.access.csv
security/seguridad.xml
views/
models/
```
