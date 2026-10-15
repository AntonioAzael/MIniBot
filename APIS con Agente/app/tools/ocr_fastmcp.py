# -*- coding: utf-8 -*-
"""
Servidor FastMCP y Utilidad Unificada de OCR para Tickets y Recibos
Compatible con agentes LLM y almacenamiento en MinIO.
"""

import os
import io
import re
import base64
from PIL import Image, ImageEnhance, ImageFilter

try:
    from fastmcp import FastMCP
    mcp = FastMCP("Lector-Tickets-OCR")
except ImportError:
    mcp = None

_motor_ddddocr = None
_motor_easyocr = None

def _obtener_motor_ocr():
    """Detecta e inicializa el mejor motor OCR disponible en el entorno."""
    global _motor_ddddocr, _motor_easyocr
    
    # Prioridad A: EasyOCR (Excelente para tickets completos)
    try:
        import easyocr
        if _motor_easyocr is None:
            _motor_easyocr = easyocr.Reader(['es', 'en'], gpu=False, verbose=False)
        return "easyocr", _motor_easyocr
    except ImportError:
        pass

    # Prioridad B: ddddocr (Ligero, ya usado en ControlSolarCorporativo)
    try:
        import ddddocr
        if _motor_ddddocr is None:
            _motor_ddddocr = ddddocr.DdddOcr(show_ad=False)
        return "ddddocr", _motor_ddddocr
    except ImportError:
        pass

    # Prioridad C: Pytesseract
    try:
        import pytesseract
        return "pytesseract", pytesseract
    except ImportError:
        pass

    raise RuntimeError(
        "No hay ningun motor de OCR instalado. Instala al menos uno con:\n"
        "  pip install ddddocr\n"
        "o\n"
        "  pip install easyocr"
    )

def preprocesar_imagen(imagen_pil: Image.Image) -> Image.Image:
    """
    Mejora la legibilidad de tickets:
    - Convierte a escala de grises.
    - Incrementa contraste para resaltar letras tenues (papel termico).
    """
    img_gray = imagen_pil.convert('L')
    enhancer = ImageEnhance.Contrast(img_gray)
    img_contrast = enhancer.enhance(1.8)
    img_sharp = img_contrast.filter(ImageFilter.SHARPEN)
    return img_sharp

def _cargar_imagen(origen: str) -> Image.Image:
    """
    Carga una imagen ya sea desde:
    - Ruta local en disco (ej. './descargas_minio/ticket_01.jpg')
    - String Base64 directo (ej. 'data:image/png;base64,...')
    """
    origen_strip = origen.strip()
    
    if origen_strip.startswith("data:image") or len(origen_strip) > 500:
        if "," in origen_strip:
            origen_strip = origen_strip.split(",", 1)[1]
        raw_bytes = base64.b64decode(origen_strip)
        return Image.open(io.BytesIO(raw_bytes))
    
    if os.path.exists(origen_strip):
        return Image.open(origen_strip)
    
    raise FileNotFoundError(f"No se encontro el archivo ni es un Base64 valido: {origen[:60]}...")

def procesar_lectura_ticket(origen_imagen: str) -> str:
    """
    Lee una imagen de ticket o recibo y devuelve el texto plano extraido.
    """
    tipo_motor, motor = _obtener_motor_ocr()
    img_original = _cargar_imagen(origen_imagen)
    img_preparada = preprocesar_imagen(img_original)

    lineas_texto = []

    if tipo_motor == "easyocr":
        buf = io.BytesIO()
        img_preparada.save(buf, format="PNG")
        resultados = motor.readtext(buf.getvalue(), detail=0)
        lineas_texto = resultados

    elif tipo_motor == "ddddocr":
        buf = io.BytesIO()
        img_preparada.save(buf, format="PNG")
        texto_raw = motor.classification(buf.getvalue())
        lineas_texto = [texto_raw]

    elif tipo_motor == "pytesseract":
        texto_raw = motor.image_to_string(img_preparada, lang='spa+eng')
        lineas_texto = [linea.strip() for linea in texto_raw.split('\n') if linea.strip()]

    texto_final = "\n".join(lineas_texto).strip()
    
    if not texto_final:
        return "[AVISO] La imagen se proceso pero no se detecto texto legible."

    return texto_final

if mcp is not None:
    @mcp.tool()
    def leer_imagen_ticket(origen_imagen: str) -> str:
        """
        Herramienta para el agente: Extrae todo el texto contenido en la imagen 
        de un ticket, nota de venta o recibo.
        """
        try:
            return procesar_lectura_ticket(origen_imagen)
        except Exception as e:
            return f"[ERROR AL LEER TICKET]: {str(e)}"

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        ruta_archivo = sys.argv[1]
        print(f"\n--- Probando lectura de: {ruta_archivo} ---")
        resultado = procesar_lectura_ticket(ruta_archivo)
        print("TEXTO EXTRAIDO:\n")
        print(resultado)
    else:
        if mcp:
            print("Iniciando servidor FastMCP de lectura de tickets...")
            mcp.run()
        else:
            print("FastMCP no esta instalado. Usa 'pip install fastmcp'.")
