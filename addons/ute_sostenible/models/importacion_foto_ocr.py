import base64
import io
import re
import unicodedata
from datetime import date
from difflib import SequenceMatcher

from odoo import fields, models


class ImportacionFotoOCRMixin(models.AbstractModel):
    _name = "ute_sostenible.importacion_foto_ocr.mixin"
    _description = "Herramientas OCR para importacion de pesaje desde foto"

    def _decodificar_imagen(self):
        self.ensure_one()
        contenido = self.foto_planilla
        if isinstance(contenido, str):
            contenido = contenido.encode()
        return base64.b64decode(contenido)

    def _preprocesar_imagen(self, imagen_bytes):
        metadatos = {"motor": "sin_preprocesamiento", "disponible": False}
        try:
            from PIL import Image, ImageEnhance, ImageFilter, ImageOps
        except Exception as exc:
            metadatos["mensaje"] = f"Pillow no disponible: {exc}"
            return imagen_bytes, metadatos
        try:
            imagen = Image.open(io.BytesIO(imagen_bytes))
            metadatos.update(
                {
                    "motor": "Pillow",
                    "disponible": True,
                    "modo_original": imagen.mode,
                    "tamano_original": imagen.size,
                }
            )
            imagen = ImageOps.exif_transpose(imagen).convert("L")
            imagen = ImageOps.autocontrast(imagen)
            imagen = ImageEnhance.Contrast(imagen).enhance(1.8)
            imagen = imagen.filter(ImageFilter.MedianFilter(size=3))
            imagen = imagen.point(lambda pixel: 255 if pixel > 175 else 0)
            salida = io.BytesIO()
            imagen.save(salida, format="PNG")
            metadatos["tamano_procesado"] = imagen.size
            return salida.getvalue(), metadatos
        except Exception as exc:
            metadatos["mensaje"] = f"No se pudo preprocesar la imagen: {exc}"
            return imagen_bytes, metadatos

    def _extraer_texto_ocr(self, imagen_bytes):
        metadatos = {
            "disponible": False,
            "motor": False,
            "mensaje": "OCR no disponible. Puede ingresar las líneas manualmente en la tabla.",
        }
        try:
            import pytesseract
            from PIL import Image
        except Exception as exc:
            metadatos["mensaje"] = f"OCR no disponible. Puede ingresar las líneas manualmente en la tabla. Detalle: {exc}"
            return "", metadatos
        try:
            imagen = Image.open(io.BytesIO(imagen_bytes))
            config = "--psm 6"
            texto = pytesseract.image_to_string(imagen, lang="spa+eng", config=config)
            metadatos.update({"disponible": True, "motor": "pytesseract", "config": config})
            try:
                data = pytesseract.image_to_data(imagen, lang="spa+eng", config=config, output_type=pytesseract.Output.DICT)
                confianzas = [
                    float(valor)
                    for valor in data.get("conf", [])
                    if str(valor).replace(".", "", 1).lstrip("-").isdigit() and float(valor) >= 0
                ]
                if confianzas:
                    metadatos["confianza_promedio"] = round(sum(confianzas) / len(confianzas), 2)
            except Exception as exc:
                metadatos["detalle_confianza"] = str(exc)
            return texto or "", metadatos
        except Exception as exc:
            metadatos["mensaje"] = f"No se pudo ejecutar OCR: {exc}"
            return "", metadatos

    def _extraer_tabla_por_celdas(self, imagen_bytes):
        metadatos = {"disponible": False, "motor": False, "mensaje": False}
        try:
            import cv2
            import numpy as np
            import pytesseract
            from PIL import Image
        except Exception as exc:
            metadatos["mensaje"] = f"Lectura por celdas no disponible: {exc}"
            return [], metadatos
        try:
            arreglo = np.frombuffer(imagen_bytes, dtype=np.uint8)
            imagen = cv2.imdecode(arreglo, cv2.IMREAD_GRAYSCALE)
            if imagen is None:
                metadatos["mensaje"] = "No se pudo abrir la imagen con OpenCV."
                return [], metadatos
            binaria = cv2.adaptiveThreshold(
                imagen,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                31,
                12,
            )
            ancho = imagen.shape[1]
            alto = imagen.shape[0]
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(ancho // 25, 20), 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(alto // 35, 15)))
            lineas_h = cv2.morphologyEx(binaria, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
            lineas_v = cv2.morphologyEx(binaria, cv2.MORPH_OPEN, vertical_kernel, iterations=1)
            tabla = cv2.add(lineas_h, lineas_v)
            contornos, _ = cv2.findContours(tabla, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            cajas = []
            for contorno in contornos:
                x, y, w, h = cv2.boundingRect(contorno)
                if 20 <= w <= ancho * 0.95 and 12 <= h <= alto * 0.25:
                    cajas.append((x, y, w, h))
            cajas = sorted(cajas, key=lambda caja: (caja[1], caja[0]))
            filas_cajas = []
            for caja in cajas:
                agregada = False
                for fila in filas_cajas:
                    y_promedio = sum(c[1] for c in fila) / len(fila)
                    if abs(caja[1] - y_promedio) <= max(caja[3], 14):
                        fila.append(caja)
                        agregada = True
                        break
                if not agregada:
                    filas_cajas.append([caja])
            filas_detectadas = []
            for fila in filas_cajas:
                fila = sorted(fila, key=lambda caja: caja[0])
                if len(fila) < 6:
                    continue
                textos = []
                for x, y, w, h in fila[:12]:
                    margen = 2
                    recorte = imagen[max(y - margen, 0) : min(y + h + margen, alto), max(x - margen, 0) : min(x + w + margen, ancho)]
                    texto_celda = pytesseract.image_to_string(
                        Image.fromarray(recorte),
                        lang="spa+eng",
                        config="--psm 7",
                    )
                    textos.append(self._limpiar_texto(texto_celda))
                if self._normalizar(textos[0]) in ("n", "no", "numero") or "fecha" in self._normalizar(" ".join(textos)):
                    continue
                numero = False
                partes = textos[:11]
                if textos and re.fullmatch(r"\d{1,2}", textos[0] or ""):
                    numero = int(textos[0])
                    partes = textos[1:12]
                fila_map = self._fila_desde_partes(numero, partes, " | ".join(textos))
                if fila_map:
                    filas_detectadas.append(fila_map)
                if len(filas_detectadas) >= 28:
                    break
            metadatos.update(
                {
                    "disponible": True,
                    "motor": "opencv+pytesseract",
                    "celdas_detectadas": len(cajas),
                    "filas_detectadas": len(filas_detectadas),
                }
            )
            return filas_detectadas, metadatos
        except Exception as exc:
            metadatos["mensaje"] = f"No se pudo leer la tabla por celdas: {exc}"
            return [], metadatos

    def _detectar_filas_tabla(self, texto):
        filas = []
        for texto_linea in (texto or "").splitlines():
            texto_limpio = self._limpiar_texto(texto_linea)
            if not texto_limpio:
                continue
            fila = self._mapear_columnas(texto_limpio)
            if fila:
                filas.append(fila)
        return filas[:28]

    def _mapear_columnas(self, texto_linea):
        partes = [parte.strip() for parte in re.split(r"\t+|\s{2,}", texto_linea) if parte.strip()]
        numero = False
        if partes and re.fullmatch(r"\d{1,2}", partes[0]):
            numero = int(partes.pop(0))
        if not numero:
            coincidencia = re.match(r"^\s*(\d{1,2})[\).\-\s]+(.+)$", texto_linea)
            if coincidencia:
                numero = int(coincidencia.group(1))
                resto = coincidencia.group(2)
                partes = [parte.strip() for parte in re.split(r"\t+|\s{2,}", resto) if parte.strip()]
        if numero and 1 <= numero <= 28:
            return self._fila_desde_partes(numero, partes, texto_linea)
        coincidencia_fecha = re.search(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", texto_linea)
        if coincidencia_fecha:
            return self._fila_desde_partes(False, partes or [texto_linea], texto_linea)
        return False

    def _fila_desde_partes(self, numero, partes, texto_original):
        valores = {
            "numero_linea": numero,
            "texto_original_linea": texto_original,
            "confianza_ocr": 0.6,
        }
        columnas = [
            "fecha",
            "hora",
            "responsable_texto",
            "edificio_texto",
            "piso_texto",
            "estacion",
            "bolsa_azul",
            "bolsa_negra",
            "bolsa_verde",
            "observaciones",
            "firma_texto",
        ]
        for indice, columna in enumerate(columnas):
            if indice < len(partes):
                valores[columna] = partes[indice]
        if len(partes) < 6:
            valores["observaciones"] = texto_original
        return valores

    def _crear_lineas_desde_filas(self, filas):
        Linea = self.env["ute_sostenible.importacion_foto_pesaje_linea"]
        for indice, fila in enumerate(filas, start=1):
            valores = self._valores_linea_desde_fila(fila, indice)
            linea = Linea.create(valores)
            linea._autocompletar_y_clasificar()

    def _crear_lineas_manuales(self):
        Linea = self.env["ute_sostenible.importacion_foto_pesaje_linea"]
        for numero in range(1, 29):
            Linea.create(
                {
                    "importacion_id": self.id,
                    "numero_linea": numero,
                    "crear_registro": False,
                    "estado_linea": "revisar",
                    "mensaje_error": "OCR no disponible o no detectó esta línea. Complete manualmente si corresponde.",
                }
            )

    def _valores_linea_desde_fila(self, fila, indice):
        fecha = self._parsear_fecha(fila.get("fecha"))
        hora = self._parsear_hora(fila.get("hora"))
        bolsa_azul = self._parsear_peso(fila.get("bolsa_azul"))
        bolsa_negra = self._parsear_peso(fila.get("bolsa_negra"))
        bolsa_verde = self._parsear_peso(fila.get("bolsa_verde"))
        responsable = self._buscar_responsable(fila.get("responsable_texto"))
        bloque = self._buscar_bloque(fila.get("edificio_texto"))
        piso = self._buscar_piso(fila.get("piso_texto"), bloque)
        punto = self._buscar_punto_ecologico(fila.get("estacion"), bloque, piso)
        return {
            "importacion_id": self.id,
            "numero_linea": fila.get("numero_linea") or indice,
            "fecha": fecha,
            "hora": hora,
            "responsable_texto": fila.get("responsable_texto"),
            "responsable_id": responsable.id if responsable else False,
            "edificio_texto": fila.get("edificio_texto"),
            "bloque_id": bloque.id if bloque else False,
            "piso_texto": fila.get("piso_texto"),
            "piso_id": piso.id if piso else False,
            "estacion": fila.get("estacion"),
            "punto_ecologico_id": punto.id if punto else False,
            "bolsa_azul": bolsa_azul,
            "bolsa_negra": bolsa_negra,
            "bolsa_verde": bolsa_verde,
            "observaciones": fila.get("observaciones"),
            "firma_texto": fila.get("firma_texto"),
            "confianza_ocr": fila.get("confianza_ocr", 0.6),
            "texto_original_linea": fila.get("texto_original_linea"),
        }

    def _parsear_fecha(self, valor):
        valor = self._limpiar_texto(valor)
        if not valor:
            return False
        coincidencia = re.search(r"(\d{1,4})[/-](\d{1,2})[/-]?(\d{0,4})", valor)
        if not coincidencia:
            return False
        primero, segundo, tercero = coincidencia.groups()
        actual = fields.Date.context_today(self)
        try:
            if len(primero) == 4:
                anio, mes, dia = int(primero), int(segundo), int(tercero)
            else:
                dia, mes = int(primero), int(segundo)
                anio = int(tercero) if tercero else actual.year
                if anio < 100:
                    anio += 2000
            return date(anio, mes, dia)
        except Exception:
            return False

    def _parsear_hora(self, valor):
        valor = self._limpiar_texto(valor)
        if not valor:
            return 0.0
        coincidencia = re.search(r"\b(\d{1,2})[:hH](\d{2})\b", valor)
        if coincidencia:
            horas = int(coincidencia.group(1))
            minutos = int(coincidencia.group(2))
            if 0 <= horas <= 23 and 0 <= minutos <= 59:
                return horas + minutos / 60.0
        coincidencia_decimal = re.search(r"\b(\d{1,2})[,.](\d{1,2})\b", valor)
        if coincidencia_decimal:
            horas = int(coincidencia_decimal.group(1))
            decimal = int(coincidencia_decimal.group(2))
            if 0 <= horas <= 23:
                return horas + decimal / 100.0
        return 0.0

    def _parsear_peso(self, valor):
        valor = self._normalizar_peso(valor)
        if not valor:
            return 0.0
        coincidencia = re.search(r"-?\d+(?:[.,]\d+)?", valor)
        if not coincidencia:
            return 0.0
        try:
            peso = float(coincidencia.group(0).replace(",", "."))
        except Exception:
            return 0.0
        return max(peso, 0.0)

    def _buscar_responsable(self, texto):
        texto = self._limpiar_texto(texto)
        if not texto:
            return self.env["res.users"]
        usuario = self.env["res.users"].search([("name", "=ilike", texto)], limit=1)
        if usuario:
            return usuario
        partner = self._buscar_aproximado("res.partner", texto, ["name"])
        return partner.user_ids[:1] if partner and partner.user_ids else self.env["res.users"]

    def _buscar_bloque(self, texto):
        texto = self._limpiar_texto(texto)
        if not texto:
            return self.env["ute_sostenible.bloque"]
        Bloque = self.env["ute_sostenible.bloque"]
        bloque = Bloque.search([("nombre", "=ilike", texto)], limit=1)
        if bloque:
            return bloque
        if re.fullmatch(r"[A-Za-z]", texto):
            bloque = Bloque.search([("nombre", "=ilike", f"Bloque {texto}")], limit=1)
            if bloque:
                return bloque
        return self._buscar_aproximado("ute_sostenible.bloque", texto, ["nombre"])

    def _buscar_piso(self, texto, bloque=False):
        texto = self._normalizar_piso(texto)
        if not texto:
            return self.env["ute_sostenible.piso"]
        dominio = [("nombre", "=ilike", texto)]
        if bloque:
            dominio.append(("bloque_id", "=", bloque.id))
        Piso = self.env["ute_sostenible.piso"]
        piso = Piso.search(dominio, limit=1)
        if piso:
            return piso
        dominio = []
        if bloque:
            dominio.append(("bloque_id", "=", bloque.id))
        candidatos = Piso.search(dominio)
        return self._elegir_aproximado(candidatos, texto, ["nombre"])

    def _buscar_punto_ecologico(self, estacion, bloque=False, piso=False):
        estacion = self._limpiar_texto(estacion)
        Punto = self.env["ute_sostenible.punto_ecologico"]
        dominio = []
        if bloque:
            dominio.append(("bloque_id", "=", bloque.id))
        if piso:
            dominio.append(("piso_id", "=", piso.id))
        candidatos = Punto.search(dominio)
        if estacion:
            punto = self._elegir_aproximado(candidatos, estacion, ["nombre", "descripcion"])
            if punto:
                return punto
        if len(candidatos) == 1:
            return candidatos
        return Punto

    def _buscar_aproximado(self, modelo, texto, campos):
        return self._elegir_aproximado(self.env[modelo].search([]), texto, campos)

    def _elegir_aproximado(self, registros, texto, campos):
        texto_norm = self._normalizar(texto)
        mejor = self.env[registros._name] if registros else False
        mejor_score = 0.0
        for registro in registros:
            for campo in campos:
                valor = self._normalizar(registro[campo] or "")
                if not valor:
                    continue
                score = 1.0 if valor == texto_norm else SequenceMatcher(None, texto_norm, valor).ratio()
                if texto_norm and texto_norm in valor:
                    score = max(score, 0.88)
                if score > mejor_score:
                    mejor = registro
                    mejor_score = score
        return mejor if mejor_score >= 0.72 else self.env[registros._name]

    def _normalizar_piso(self, texto):
        texto = self._limpiar_texto(texto)
        normalizado = self._normalizar(texto)
        alias = {
            "pb": "PB",
            "p_b": "PB",
            "planta_baja": "PB",
            "1": "1er piso",
            "1ero": "1er piso",
            "primer_piso": "1er piso",
            "2": "2do piso",
            "2do": "2do piso",
            "segundo_piso": "2do piso",
            "3": "3er piso",
            "3ro": "3er piso",
            "tercer_piso": "3er piso",
        }
        return alias.get(normalizado, texto)

    def _normalizar_peso(self, texto):
        texto = self._limpiar_texto(texto).lower()
        return re.sub(r"\b(kg|kgs|kilos|kilogramos)\b", "", texto).strip()

    def _limpiar_texto(self, texto):
        return re.sub(r"\s+", " ", str(texto or "").replace("\xa0", " ")).strip()

    def _normalizar(self, texto):
        texto = unicodedata.normalize("NFKD", self._limpiar_texto(texto).lower())
        texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
        return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")
