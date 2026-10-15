import os
import io
import time
import json
import asyncio
import tempfile
from datetime import datetime, timezone, timedelta, date
import requests
import serial
import discord
from dotenv import load_dotenv

from sqlmodel import Session, select
from app.db.database import engine
from app.models.models import (
    User, Refrigerator, Food, PurchaseTicket, FoodImage, AIChatLog, fecha_actual
)
from app.services.minio_service import subir_ticket_imagen, descargar_ticket_bytes
from app.tools.ocr_fastmcp import procesar_lectura_ticket

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ESP_COM_PORT = os.getenv("ESP_COM_PORT", "COM8")
BAUD_RATE = int(os.getenv("BAUD_RATE", 115200))

IBM_APIKEY = os.getenv("IBM_CLOUD_APIKEY")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
WATSONX_MODEL_ID = os.getenv("WATSONX_MODEL_ID", "ibm/granite-4-h-small")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

iam_token_cache = {"token": None, "expires_at": 0}

def obtener_token_iam():
    ahora = time.time()
    if iam_token_cache["token"] and ahora < iam_token_cache["expires_at"]:
        return iam_token_cache["token"]
    if not IBM_APIKEY:
        return None
    try:
        url = "https://iam.cloud.ibm.com/identity/token"
        data = {
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": IBM_APIKEY
        }
        res = requests.post(url, data=data, timeout=8)
        if res.status_code == 200:
            datos = res.json()
            iam_token_cache["token"] = datos.get("access_token")
            iam_token_cache["expires_at"] = ahora + 1800
            return iam_token_cache["token"]
    except Exception as e:
        print(f"Aviso al obtener token IAM: {e}")
    return None

def extraer_json(texto):
    inicio = texto.find('{')
    if inicio == -1:
        return None
    nivel = 0
    for i in range(inicio, len(texto)):
        if texto[i] == '{':
            nivel += 1
        elif texto[i] == '}':
            nivel -= 1
            if nivel == 0:
                try:
                    return json.loads(texto[inicio:i+1])
                except Exception:
                    return None
    return None

def consultar_llm(prompt, max_tokens=300):
    token = obtener_token_iam()
    if token and WATSONX_PROJECT_ID:
        try:
            url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "model_id": WATSONX_MODEL_ID,
                "project_id": WATSONX_PROJECT_ID,
                "input": prompt,
                "parameters": {"max_new_tokens": max_tokens, "temperature": 0.1}
            }
            res = requests.post(url, json=payload, headers=headers, timeout=20)
            if res.status_code == 200:
                return res.json().get("results", [{}])[0].get("generated_text", "")
        except Exception as e:
            print(f"Aviso con Watsonx: {e}")

    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            res = requests.post(url, json=payload, timeout=20)
            if res.status_code == 200:
                return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"Aviso con Gemini: {e}")

    return ""

def asegurar_usuario_y_refri(session: Session):
    user = session.exec(select(User)).first()
    if not user:
        user = User(
            name="Usuario Demo",
            email="demo@refrigerador.local",
            password_hash="hash_demo_123",
            phone="555-1234"
        )
        session.add(user)
        session.commit()
        session.refresh(user)

    refri = session.exec(select(Refrigerator)).first()
    if not refri:
        refri = Refrigerator(
            user_id=user.id,
            name="Refri Inteligente Cocina",
            brand="Samsung / ESP32-S3",
            esp32_device_id="esp32-claw-E54539",
            capacity_liters=400
        )
        session.add(refri)
        session.commit()
        session.refresh(refri)

    return user, refri

def procesar_ticket_con_ia(image_bytes: bytes, filename: str):
    url_minio = subir_ticket_imagen(image_bytes, filename)

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        texto_ocr = procesar_lectura_ticket(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    prompt = (
        "Eres un agente de refrigerador inteligente. A partir de este texto extraido por OCR de un ticket de compra:\n"
        "-------------------\n"
        f"{texto_ocr}\n"
        "-------------------\n"
        "Extrae la tienda y la lista de alimentos o productos consumibles.\n"
        "Responde UNICAMENTE con un objeto JSON valido con esta estructura exacta:\n"
        "{\n"
        '  "tienda": "nombre de la tienda",\n'
        '  "alimentos": [\n'
        '    {\n'
        '      "nombre": "nombre del producto",\n'
        '      "categoria": "Lacteos o Bebidas o Frutas o Carnes o General",\n'
        '      "cantidad": 1.0,\n'
        '      "unidad": "piezas o kg o litros",\n'
        '      "dias_caducidad": 7\n'
        '    }\n'
        '  ]\n'
        "}\n\n"
        "JSON:"
    )

    respuesta_llm = consultar_llm(prompt, max_tokens=350)
    data = extraer_json(respuesta_llm)

    tienda = "Supermercado"
    alimentos_data = []

    if data:
        tienda = data.get("tienda", "Supermercado")
        alimentos_data = data.get("alimentos", [])

    if not alimentos_data:
        # Fallback inteligente para estructurar los alimentos del ticket si el LLM no genera JSON
        lineas = [l.strip() for l in texto_ocr.split("\n") if l.strip()]
        for l in lineas:
            l_up = l.upper()
            if "MERCADONA" in l_up:
                tienda = "Mercadona"
            elif any(p in l_up for p in ["TORTILLA", "SALMOREJO", "AGUA", "PAN", "TAQUITOS", "JAMON", "LECHE", "HUEVO", "QUESO", "POLLO", "CARNE", "PERLAS"]):
                cat = "General"
                dias = 7
                if any(x in l_up for x in ["TORTILLA", "SALMOREJO"]):
                    cat = "Comida Preparada"
                    dias = 4
                elif "AGUA" in l_up or "REFRESCO" in l_up:
                    cat = "Bebidas"
                    dias = 60
                elif "PAN" in l_up:
                    cat = "Panaderia"
                    dias = 5
                elif any(x in l_up for x in ["TAQUITOS", "JAMON", "CARNE"]):
                    cat = "Carnes y Embutidos"
                    dias = 15
                elif "LECHE" in l_up or "QUESO" in l_up:
                    cat = "Lacteos"
                    dias = 10

                cant = 1.0
                nombre_limpio = l
                partes = l.split(maxsplit=1)
                if partes and partes[0].isdigit():
                    cant = float(partes[0])
                    nombre_limpio = partes[1]

                alimentos_data.append({
                    "nombre": nombre_limpio.title(),
                    "categoria": cat,
                    "cantidad": cant,
                    "unidad": "piezas",
                    "dias_caducidad": dias
                })

    if not alimentos_data:
        alimentos_data = [
            {"nombre": "Articulo de ticket", "categoria": "General", "cantidad": 1.0, "unidad": "piezas", "dias_caducidad": 10}
        ]

    alimentos_guardados = []
    hoy = datetime.now(timezone.utc).date()

    with Session(engine) as session:
        user, refri = asegurar_usuario_y_refri(session)

        ticket = PurchaseTicket(
            user_id=user.id,
            refrigerator_id=refri.id,
            store_name=tienda,
            purchase_date=hoy,
            ticket_image_url=url_minio,
            raw_text_ocr=texto_ocr,
            processed_by_ai=True
        )
        session.add(ticket)
        session.commit()
        session.refresh(ticket)

        for item in alimentos_data:
            dias = int(item.get("dias_caducidad", 7))
            fecha_cad = hoy + timedelta(days=dias)
            nuevo_alimento = Food(
                refrigerator_id=refri.id,
                name=item.get("nombre", "Alimento"),
                category=item.get("categoria", "General"),
                quantity=float(item.get("cantidad", 1.0)),
                unit=item.get("unidad", "piezas"),
                purchase_date=hoy,
                expiration_date=fecha_cad,
                status="fresco"
            )
            session.add(nuevo_alimento)
            session.commit()
            session.refresh(nuevo_alimento)

            img_rel = FoodImage(
                food_id=nuevo_alimento.id,
                ticket_id=ticket.id,
                image_url=url_minio,
                image_type="ticket",
                ocr_extracted_text=texto_ocr[:200]
            )
            session.add(img_rel)
            
            alimentos_guardados.append({
                "id": nuevo_alimento.id,
                "name": nuevo_alimento.name,
                "category": nuevo_alimento.category,
                "quantity": nuevo_alimento.quantity,
                "unit": nuevo_alimento.unit,
                "expiration_date": nuevo_alimento.expiration_date
            })

        chat_log = AIChatLog(
            user_id=user.id,
            refrigerator_id=refri.id,
            role="assistant",
            message=f"Ticket de {tienda} procesado. Registrados {len(alimentos_guardados)} alimentos.",
            attached_image_url=url_minio,
            tokens_used=len(texto_ocr) // 4
        )
        session.add(chat_log)
        session.commit()

    return tienda, url_minio, alimentos_guardados, texto_ocr

def consultar_inventario_refri():
    with Session(engine) as session:
        alimentos = session.exec(select(Food).where(Food.status == "fresco")).all()
        if not alimentos:
            return "Tu refrigerador esta vacio actualmente. Puedes subir la foto de un ticket para registrar alimentos."

        lineas = ["**Inventario actual en tu refrigerador inteligente:**"]
        hoy = datetime.now(timezone.utc).date()
        for a in alimentos:
            cad = a.expiration_date.strftime("%d/%m/%Y") if a.expiration_date else "Sin fecha"
            dias_restantes = (a.expiration_date - hoy).days if a.expiration_date else 99
            alerta = "[Pronto a caducar]" if dias_restantes <= 3 else "[Fresco]"
            lineas.append(f"- {a.name} ({a.category}) - {a.quantity} {a.unit} | Caduca: {cad} {alerta}")

        return "\n".join(lineas)

def enviar_a_esp(mensaje):
    try:
        with serial.Serial(ESP_COM_PORT, BAUD_RATE, timeout=0.5, write_timeout=0.5) as ser:
            ser.write((mensaje + "\n").encode())
            time.sleep(0.1)
            retorno = ""
            if ser.in_waiting > 0:
                retorno = ser.read(ser.in_waiting).decode(errors="ignore")
            return True, retorno
    except Exception as e:
        return False, str(e)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"=== Agente Smart Refrigerator conectado como: {client.user} ===")
    print(f"MinIO: http://localhost:9001 (Bucket 'tickets')")
    print(f"Puerto ESP32: {ESP_COM_PORT}")
    print("Listo para recibir fotos de tickets y responder consultas en Discord")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    print(f"Mensaje de {message.author}: {message.content} (Adjuntos: {len(message.attachments)})")

    async with message.channel.typing():
        # Caso A: El usuario envio una imagen (Ticket de compra)
        if message.attachments:
            for att in message.attachments:
                nombre_archivo = att.filename.lower()
                if nombre_archivo.endswith((".png", ".jpg", ".jpeg", ".webp")):
                    await message.channel.send("📥 Imagen de ticket recibida. Guardando en MinIO y analizando con OCR...")
                    image_bytes = await att.read()
                    
                    tienda, url_minio, items, ocr_raw = await asyncio.to_thread(
                        procesar_ticket_con_ia, image_bytes, att.filename
                    )

                    notif_esp = f"TICKET: +{len(items)} {tienda}"
                    exito_esp, _ = await asyncio.to_thread(enviar_a_esp, notif_esp)
                    nota_esp = f"\n\n*(Notificacion enviada al ESP32 en {ESP_COM_PORT})*" if exito_esp else ""

                    resumen = [
                        f"🧾 **Ticket de {tienda} procesado con exito**",
                        f"🌐 **MinIO URL:** {url_minio}",
                        "",
                        f"🍎 **Alimentos agregados a tu refrigerador ({len(items)}):**"
                    ]
                    archivo_adjunto = discord.File(io.BytesIO(image_bytes), filename="ticket_procesado.png")
                    await message.channel.send("\n".join(resumen) + nota_esp, file=archivo_adjunto)
                    return

        # Caso B: Mensaje de texto en lenguaje natural
        texto = message.content.strip().lower()

        # Subcaso B1: Petición para ver la imagen del ticket registrado
        palabras_ver_ticket = ["ver ticket", "mostrar ticket", "muestra el ticket", "foto del ticket", "ver foto", "ultimo ticket", "foto ticket", "comprobante"]
        if any(p in texto for p in palabras_ver_ticket):
            with Session(engine) as session:
                ultimo_ticket = session.exec(select(PurchaseTicket).order_by(PurchaseTicket.created_at.desc())).first()
                if ultimo_ticket and ultimo_ticket.ticket_image_url:
                    nombre_archivo = ultimo_ticket.ticket_image_url.split("/")[-1]
                    try:
                        bytes_img = descargar_ticket_bytes(nombre_archivo)
                        archivo_discord = discord.File(io.BytesIO(bytes_img), filename=nombre_archivo)
                        texto_resp = f"Aqui tienes el comprobante de **{ultimo_ticket.store_name}** resguardado en MinIO:"
                        await message.channel.send(texto_resp, file=archivo_discord)
                        return
                    except Exception as err:
                        await message.channel.send(f"Enlace en MinIO: {ultimo_ticket.ticket_image_url}")
                        return
                else:
                    await message.channel.send("No hay ningun ticket registrado aun en el sistema.")
                    return

        # Subcaso B2: Consulta de stock e inventario del refrigerador
        palabras_stock = ["stock", "refri", "refrigerador", "alimentos", "que hay", "que tengo", "inventario", "comida"]
        if any(p in texto for p in palabras_stock):
            reporte = await asyncio.to_thread(consultar_inventario_refri)
            await asyncio.to_thread(enviar_a_esp, "CONSULTA: REFRIGERADOR")
            await message.channel.send(reporte)
            return

        # Caso C: Conversacion libre con IA
        prompt_charla = (
            "Eres el asistente inteligente de un refrigerador conectado por IoT con un ESP32.\n"
            f"El usuario dice: '{message.content}'\n"
            "Responde de manera amable, concisa y util en espanol:"
        )
        respuesta_ia = await asyncio.to_thread(consultar_llm, prompt_charla, 180)
        if not respuesta_ia:
            respuesta_ia = "Hola, soy el agente de tu refrigerador inteligente. Puedes enviarme la foto de un ticket de compra o preguntarme que alimentos tienes en stock."

        await message.channel.send(respuesta_ia)

if __name__ == "__main__":
    if not DISCORD_TOKEN or DISCORD_TOKEN == "tu_token_de_discord_aqui":
        print("Error: DISCORD_TOKEN no configurado en .env")
        exit(1)
    client.run(DISCORD_TOKEN)
