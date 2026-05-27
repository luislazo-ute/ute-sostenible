# Importacion desde foto

La importacion desde foto permite cargar una imagen de la planilla fisica **Registro interno de pesaje** y convertirla en lineas revisables antes de crear registros reales.

El flujo esta disenado para que siempre exista revision humana. El OCR solo propone datos.

## Como tomar la foto

- Tome la foto de frente.
- Evite sombras, reflejos y fondos oscuros.
- No corte los bordes de la tabla.
- Use buena iluminacion.
- Mantenga la hoja lo mas plana posible.
- Evite fotos inclinadas o borrosas.
- Si puede, use una sola hoja por foto.

## Como llenar la planilla fisica

La planilla debe tener una fila por cada registro de pesaje.

Columnas esperadas:

- N°
- Fecha
- Hora
- Responsable
- Edificio
- Piso
- Estacion
- Bolsa azul
- Bolsa negra
- Bolsa verde
- Observaciones
- Firma

Recomendaciones:

1. Usar una sola fila por cada registro de pesaje.
2. No escribir dos registros en la misma fila.
3. Escribir dentro de los bordes de cada celda.
4. No invadir columnas vecinas.
5. Usar letra clara, preferiblemente mayuscula imprenta.
6. No usar abreviaturas raras.
7. La fecha debe escribirse como `DD/MM/AAAA`. Ejemplo: `25/05/2026`.
8. La hora debe escribirse en formato 24 horas. Ejemplo: `14:30`.
9. El responsable debe escribirse con el mismo nombre usado en Odoo.
10. El edificio debe escribirse igual que el bloque registrado en Odoo. Ejemplo: `Bloque A`.
11. El piso debe escribirse de forma consistente. Ejemplos validos: `PB`, `1er piso`, `2do piso`, `3er piso`.
12. La estacion debe coincidir con la ubicacion o punto ecologico registrado en Odoo.
13. Los pesos deben escribirse solo con numeros.
14. Los pesos deben estar en kilogramos.
15. Para decimales, usar preferiblemente punto. Ejemplo: `2.5`.
16. Evitar escribir `kg` dentro de las columnas de peso.
17. Si una bolsa no tiene peso, escribir `0` o dejar en blanco.
18. No usar tachones.
19. No escribir encima de lineas de la tabla.
20. La firma no sera usada como dato obligatorio; quedara respaldada en la foto.

Tambien queda disponible la guia separada:

```text
addons/ute_sostenible/docs/instrucciones_planilla_ocr.md
```

## Como procesar la foto

En Odoo:

```text
UTE Sostenible -> Operacion -> Importar desde foto
```

Pasos:

1. Crear una nueva importacion.
2. Subir o tomar la foto en el campo **Foto de la planilla**.
3. Presionar **Procesar foto**.
4. Revisar la tabla de lineas detectadas.
5. Corregir fechas, horas, edificio, piso, estacion o pesos si hace falta.
6. Presionar **Recalcular lineas** si se corrigieron datos importantes.
7. Marcar **Crear registro** solo en las lineas que deben convertirse en registros reales.
8. Presionar **Crear registros**.

## Estados de linea

### Correcto

La linea tiene datos suficientes:

- Fecha valida.
- Ubicacion minima.
- Al menos un peso mayor a cero.
- Punto ecologico encontrado.

### Revisar

La linea puede servir, pero necesita revision:

- Responsable no encontrado.
- Piso no encontrado.
- Punto ecologico no encontrado.
- La confianza OCR fue baja.
- Hay texto que pudo ser interpretado con dudas.

### Error

La linea no debe crear registro hasta corregirse:

- Esta vacia.
- No tiene fecha.
- No tiene ubicacion minima.
- No tiene peso valido en bolsa azul, negra o verde.
- Los datos no se pueden interpretar.

## Que crea Odoo

Al presionar **Crear registros**, Odoo crea un registro real en:

```text
UTE Sostenible -> Operacion -> Registros de pesaje
```

Cada linea valida crea un registro independiente.

El registro creado conserva auditoria:

- Foto original de la planilla.
- Numero de linea importada.
- Texto original detectado.
- Nombre de la importacion.
- Origen del registro: Importacion desde foto.

## Limitaciones del OCR

El OCR puede fallar si:

- La foto esta inclinada.
- La hoja esta borrosa.
- Hay sombras fuertes.
- La letra es poco clara.
- Las columnas estan muy juntas.
- La tabla esta cortada.
- El servidor no tiene motor OCR instalado.

Si no hay OCR disponible, Odoo no rompe el flujo. Muestra un mensaje:

```text
OCR no disponible. Puede ingresar las lineas manualmente en la tabla.
```

En ese caso se puede completar la tabla manualmente y crear los registros despues de revisar.

## Motor OCR

El modulo intenta usar `pytesseract` si esta instalado en el entorno del servidor.

Si `pytesseract`, Tesseract o Pillow no estan disponibles, la pantalla sigue funcionando para carga manual.

Para mejorar precision en un servidor final se recomienda instalar:

- Tesseract OCR.
- Paquetes de idioma espanol para Tesseract.
- Libreria Python `pytesseract`.
- Libreria Python `Pillow`.
