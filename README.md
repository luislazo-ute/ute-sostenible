# UTE Sostenible - Odoo 19

Repositorio para el proyecto UTE Sostenible.
Este proyecto implementa un sistema de gestión de residuos y puntos ecológicos basado en la plataforma Odoo 19, adaptado a los requerimientos de la Universidad UTE.

## 1. Levantar el ambiente local

```bash
cp .env.example .env
docker compose up -d
docker compose logs -f odoo
```

Abrir Odoo en:

```text
http://localhost:8069
```

## 2. Crear la base de datos

Usar esta contraseña maestra local:

```text
admin_ute_sostenible_2026
```

Nombre sugerido de base de datos:

```text
ute_sostenible
```

## 3. Instalar el módulo

En Odoo:

```text
Aplicaciones → Actualizar lista de aplicaciones → buscar UTE Sostenible → Instalar
```

## 4. Login con imagen de la UTE

El módulo ya incluye una pantalla de login personalizada.


## 5. Herencias usadas

Los modelos principales heredan de:

```text
ute_sostenible.modelo_base
```

Esa herencia base agrega campos comunes en español y también hereda de:

```text
mail.thread
mail.activity.mixin
```

Así los formularios tienen seguimiento, chatter y actividades.

## 6. Roles

- Usuario UTE Sostenible: registra pesajes y consulta catálogos.
- Administrador UTE Sostenible: administra catálogos, puntos ecológicos, escenarios y registros.

## 7. Modelos técnicos

```text
ute_sostenible.campus
ute_sostenible.bloque
ute_sostenible.piso
ute_sostenible.categoria
ute_sostenible.tipo_contenedor
ute_sostenible.escenario
ute_sostenible.punto_ecologico
ute_sostenible.tipo_residuo
ute_sostenible.registro_pesaje
ute_sostenible.linea_registro_pesaje
```
