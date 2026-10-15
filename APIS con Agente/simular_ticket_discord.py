# -*- coding: utf-8 -*-
"""
Script de simulacion: Procesa un ticket tal como lo haria el Agente de Discord
"""
import os
import sys
from datetime import datetime, timezone
from sqlmodel import Session, select

from app.db.database import engine
from app.models.models import Food, PurchaseTicket
from discord_agent import procesar_ticket_con_ia, consultar_inventario_refri, enviar_a_esp, ESP_COM_PORT

def main():
    ruta_ticket = r"C:\Users\bauti\Downloads\Mercadona-2025A-captura_400900.jpg"
    if not os.path.exists(ruta_ticket):
        print(f"No se encontro la imagen en: {ruta_ticket}")
        return

    print("==================================================")
    print("SIMULACION DE AGENTE DE DISCORD (PROCESANDO TICKET)")
    print("==================================================")
    print(f"1. Leyendo archivo de ticket: {ruta_ticket}")
    with open(ruta_ticket, "rb") as f:
        image_bytes = f.read()

    print(f"2. Tamano de imagen: {len(image_bytes)} bytes")
    print("3. Subiendo a MinIO, extrayendo texto con OCR y razonando con IA...")
    
    tienda, url_minio, items, ocr_raw = procesar_ticket_con_ia(
        image_bytes, os.path.basename(ruta_ticket)
    )

    print("\n---------------- RESULTADO DEL AGENTE ----------------")
    print(f"Tienda detectada: {tienda}")
    print(f"URL publica en MinIO: {url_minio}")
    print(f"Texto extraido (primeros 150 caracteres):\n{ocr_raw[:150]}...")
    print("------------------------------------------------------")

    print(f"\nAlimentos registrados en la base de datos ({len(items)}):")
    for item in items:
        cad = item["expiration_date"].strftime("%d/%m/%Y") if item.get("expiration_date") else "N/A"
        print(f"  • {item['name']} | {item['quantity']} {item['unit']} ({item['category']}) - Caduca: {cad}")

    # Notificacion al ESP32 si esta conectado
    notif_esp = f"TICKET: +{len(items)} {tienda}"
    exito_esp, retorno = enviar_a_esp(notif_esp)
    if exito_esp:
        print(f"\n[IoT] Notificacion enviada exitosamente al ESP32 en {ESP_COM_PORT}")
    else:
        print(f"\n[IoT] Aviso de puerto serial: {retorno}")

    print("\n================ CONSULTA DE INVENTARIO ================")
    print(consultar_inventario_refri())
    print("========================================================")

if __name__ == "__main__":
    main()
