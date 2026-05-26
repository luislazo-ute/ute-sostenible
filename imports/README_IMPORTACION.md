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

El campo `External ID` permite crear un identificador estable para cada registro. Ese identificador se usa despues en las columnas relacionales como:

```text
Campus/External ID
Bloque / Edificio/External ID
Piso/External ID
Categoria/External ID
Tipo de contenedor/External ID
```

Ejemplo:

```text
ute_import.campus_occidental
```

Luego, cuando se importe un bloque, se puede indicar:

```text
Campus/External ID = ute_import.campus_occidental
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
Bloque -> Bloque / Edificio/External ID
Piso -> Piso/External ID
Descripcion -> Descripcion
Categoria -> Categoria/External ID
# -> Cantidad planificada
Tipo -> Tipo de contenedor/External ID
```

El modelo no tiene un campo tecnico llamado `Ubicacion`. Para esa informacion se usa el campo:

```text
Descripcion
```

El modelo tampoco tiene un campo tecnico llamado `Cantidad`. Para esa informacion se usa:

```text
Cantidad planificada
```

## Si Odoo no encuentra una relacion

Si aparece un mensaje como que Odoo no encuentra un campus, bloque, piso, categoria o tipo de contenedor:

- Verificar que el archivo padre ya fue importado.
- Verificar que el `External ID` este escrito igual en ambos archivos.
- Evitar espacios al inicio o al final.
- Respetar mayusculas, minusculas y guiones.
- Usar el mismo prefijo, por ejemplo `ute_import.`.

Ejemplo correcto:

```text
campus_import_template.csv
External ID = ute_import.campus_occidental

bloques_import_template.csv
Campus/External ID = ute_import.campus_occidental
```

## Recomendaciones para Excel

Se puede trabajar en Excel y guardar como `.xlsx`.

Tambien se puede guardar como `.csv`. Si se usa CSV:

- Usar codificacion UTF-8.
- No cambiar los encabezados.
- No borrar la columna `External ID`.
- Importar primero pocos registros para validar el mapeo.

## Mapeo manual

Si Odoo no reconoce automaticamente una columna, seleccionarla manualmente en la pantalla de importacion.

Mapeos tecnicos utiles:

```text
External ID -> id
Nombre -> nombre
Activo -> activo
Campus/External ID -> campus_id/id
Bloque / Edificio/External ID -> bloque_id/id
Piso/External ID -> piso_id/id
Descripcion -> descripcion
Categoria/External ID -> categoria_id/id
Tipo de contenedor/External ID -> tipo_contenedor_id/id
Cantidad planificada -> cantidad_planificada
Costo unitario -> costo_unitario
```

## Validar antes de importar todo

En la pantalla de importacion de Odoo, usar la validacion previa antes de cargar todos los datos.

Si la validacion pasa, ejecutar la importacion completa.
