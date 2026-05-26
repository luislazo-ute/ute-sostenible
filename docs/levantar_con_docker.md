# Levantar UTE Sostenible con Docker

Esta guia explica como levantar el proyecto **UTE Sostenible** usando Docker Compose.

## Requisitos

- Docker instalado.
- Docker Compose disponible.
- Puerto `8069` libre para Odoo.
- Puerto `5435` libre para PostgreSQL local.

## Estructura del proyecto

La ruta del proyecto es:

```text
C:\Users\TU_USUARIO\Desktop\ute-sostenible-odoo
```

El modulo personalizado esta en:

```text
addons/ute_sostenible
```

El archivo `docker-compose.yml` monta la carpeta `addons` dentro del contenedor en:

```text
/mnt/extra-addons
```

## Servicios Docker

El proyecto define dos servicios:

- `base_datos`: PostgreSQL 16.
- `odoo`: Odoo 19.

Los contenedores se llaman:

```text
ute_sostenible_postgres
ute_sostenible_odoo
```

## Levantar el ambiente

Desde la raiz del proyecto:

```powershell
cd "$env:USERPROFILE\Desktop\ute-sostenible-odoo"
docker compose up -d
```

Verificar que los contenedores esten arriba:

```powershell
docker compose ps
```

Ver logs de Odoo:

```powershell
docker compose logs -f odoo
```

Abrir Odoo en el navegador:

```text
http://localhost:8069
```

## Crear la base de datos

Desde la pantalla inicial de Odoo, crear una base de datos.

Nombre sugerido:

```text
ute_sostenible
```

Si el proyecto usa el archivo `.env.example`, primero crear el `.env`:

```powershell
Copy-Item .env.example .env
```

La contrasena maestra local indicada para este proyecto es:

```text
admin_ute_sostenible_2026
```

## Instalar el modulo

Entrar a Odoo con el usuario administrador.

Luego ir a:

```text
Aplicaciones -> Actualizar lista de aplicaciones
```

Buscar:

```text
UTE Sostenible
```

Instalar el modulo.

## Actualizar el modulo por consola

Cuando se hacen cambios en el codigo, actualizar el modulo con:

```powershell
docker compose exec -T odoo odoo -d ute_sostenible -u ute_sostenible --stop-after-init --no-http
```

Luego reiniciar Odoo:

```powershell
docker compose restart odoo
```

## Comandos utiles

Reiniciar solo Odoo:

```powershell
docker compose restart odoo
```

Reiniciar todo:

```powershell
docker compose restart
```

Detener contenedores:

```powershell
docker compose down
```

Detener y eliminar volumenes de datos:

```powershell
docker compose down -v
```

Usar `down -v` solo si se quiere borrar la base de datos local.

## Validar antes de actualizar

Compilar Python:

```powershell
py -3 -m compileall .\addons\ute_sostenible
```

Validar XML si `xmllint` esta instalado:

```powershell
Get-ChildItem .\addons\ute_sostenible -Recurse -Filter *.xml | ForEach-Object {
    xmllint --noout $_.FullName
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
```

Buscar referencias antiguas a modelos eliminados:

```powershell
Get-ChildItem .\addons\ute_sostenible -Recurse -File | Select-String -Pattern "escenario|escenario_id|ute_sostenible\.escenario"
```

## Flujo funcional actual

El flujo principal del modulo es:

```text
Campus -> Bloque / Edificio -> Piso -> Punto ecologico -> Registro de pesaje
```

Tambien incluye catalogos de:

- Categorias.
- Tipos de contenedor.
- Tipos de residuo.

## Problemas comunes

Si Odoo no muestra el modulo:

- Revisar que `./addons` este montado en `/mnt/extra-addons`.
- Revisar que `addons_path` incluya `/mnt/extra-addons`.
- Actualizar la lista de aplicaciones.
- Reiniciar el contenedor `odoo`.

Si aparece un error despues de cambiar vistas o modelos:

```powershell
docker compose logs --tail=120 odoo
```

Si el navegador queda en una accion vieja:

```text
http://localhost:8069/odoo
```

Luego hacer recarga fuerte del navegador.
