# Importacion masiva desde Odoo

Estas plantillas estan pensadas para usar la importacion estandar de Odoo:

```text
Lista del modelo -> Accion -> Importar registros / Subir archivo de datos
```

No se cargan datos XML desde el modulo. Los archivos de esta carpeta son solo plantillas para que el administrador las use desde la interfaz.

## Orden correcto de importacion

Importar en este orden para que las relaciones Many2one existan antes de usarlas:

1. `campus_import_template.csv`
2. `bloques_import_template.csv`
3. `pisos_import_template.csv`
4. `categorias_import_template.csv`
5. `tipos_contenedor_import_template.csv`
6. `tipos_residuo_import_template.csv`
7. `puntos_ecologicos_import_template.csv`

## Importante en servidor nuevo

En un servidor nuevo, no crear manualmente los registros padre antes de importar.

Primero importar `campus_import_template.csv`. Ese archivo crea los campus junto con su `id` externo, por ejemplo:

```text
ute_import.campus_occidental
ute_import.campus_matriz
```

Luego `bloques_import_template.csv` puede usar esos valores en `campus_id/id`.

Si se crean los campus manualmente desde la interfaz, Odoo crea el registro visible, pero no crea automaticamente el `id` externo. En ese caso, al importar bloques, pisos o puntos ecologicos puede aparecer un error indicando que no encuentra la relacion.

Para evitar ese problema:

- En base limpia: importar siempre desde el primer archivo, empezando por Campus.
- Si alguien ya creo datos manuales: borrar esos datos de prueba o asignar los IDs externos antes de importar relaciones.

## Como entrar a cada lista

Desde Odoo:

```text
UTE Sostenible -> Configuracion -> Campus
UTE Sostenible -> Configuracion -> Bloques / Edificios
UTE Sostenible -> Configuracion -> Pisos
UTE Sostenible -> Configuracion -> Categorias
UTE Sostenible -> Configuracion -> Tipos de contenedor
UTE Sostenible -> Configuracion -> Tipos de residuo
UTE Sostenible -> Operacion -> Puntos ecologicos
```

En cada pantalla usar:

```text
Accion -> Importar registros
```

Luego subir un archivo `.csv` o `.xlsx`.

## Campos de las plantillas

Las columnas usan nombres compatibles con el importador de Odoo.

El campo `id` permite crear un identificador externo estable para cada registro. Ese identificador se usa despues en las columnas relacionales como:

```text
campus_id/id
bloque_id/id
piso_id/id
categoria_id/id
tipo_contenedor_id/id
```

Ejemplo:

```text
ute_import.campus_occidental
```

Luego, cuando se importe un bloque, se puede indicar:

```text
campus_id/id = ute_import.campus_occidental
```

Asi Odoo relaciona el bloque con el campus correcto sin depender del nombre visible.

## Equivalencias importantes

En el Excel original aparecen columnas como:

```text
Bloque
Piso
Descripcion
Categoria
#
Tipo
```

Para importar puntos ecologicos, usar estas equivalencias:

```text
Bloque -> bloque_id/id
Piso -> piso_id/id
Descripcion -> descripcion
Categoria -> categoria_id/id
# -> cantidad_planificada
Tipo -> tipo_contenedor_id/id
```

El modelo no tiene un campo tecnico llamado `Ubicacion`. Para esa informacion se usa el campo:

```text
descripcion
```

El modelo tampoco tiene un campo tecnico llamado `Cantidad`. Para esa informacion se usa:

```text
cantidad_planificada
```

## Si Odoo no encuentra una relacion

Si aparece un mensaje como que Odoo no encuentra un campus, bloque, piso, categoria o tipo de contenedor:

- Verificar que el archivo padre ya fue importado.
- Verificar que el `id` este escrito igual en ambos archivos.
- Evitar espacios al inicio o al final.
- Respetar mayusculas, minusculas y guiones.
- Usar el mismo prefijo, por ejemplo `ute_import.`.

Ejemplo correcto:

```text
campus_import_template.csv
id = ute_import.campus_occidental

bloques_import_template.csv
campus_id/id = ute_import.campus_occidental
```

## Recomendaciones para Excel

Se puede trabajar en Excel y guardar como `.xlsx`.

Tambien se puede guardar como `.csv`. Si se usa CSV:

- Usar codificacion UTF-8.
- No cambiar los encabezados.
- No borrar la columna `id`.
- Importar primero pocos registros para validar el mapeo.

## Mapeo manual

Si Odoo no reconoce automaticamente una columna, seleccionarla manualmente en la pantalla de importacion.

Mapeos tecnicos utiles:

```text
id -> ID externo
nombre -> Nombre
activo -> Activo
campus_id/id -> Campus / ID externo
bloque_id/id -> Bloque / Edificio / ID externo
piso_id/id -> Piso / ID externo
descripcion -> Descripcion
categoria_id/id -> Categoria / ID externo
tipo_contenedor_id/id -> Tipo de contenedor / ID externo
cantidad_planificada -> Cantidad planificada
costo_unitario -> Costo unitario
```

## Validar antes de importar todo

En la pantalla de importacion de Odoo, usar la validacion previa antes de cargar todos los datos.

Si la validacion pasa, ejecutar la importacion completa.
