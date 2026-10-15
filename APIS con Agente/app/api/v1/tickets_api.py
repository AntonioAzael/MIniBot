import os
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.models import PurchaseTicket, Food, FoodImage
from app.services.minio_service import subir_ticket_imagen
from app.tools.ocr_fastmcp import procesar_lectura_ticket

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.get("/", response_model=List[PurchaseTicket])
def listar_tickets(session: Session = Depends(get_session)):
    tickets = session.exec(select(PurchaseTicket)).all()
    return tickets

@router.get("/{ticket_id}", response_model=PurchaseTicket)
def obtener_ticket(ticket_id: str, session: Session = Depends(get_session)):
    ticket = session.get(PurchaseTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket

@router.post("/upload")
async def subir_ticket(
    user_id: str = Form(...),
    refrigerator_id: str = Form(...),
    store_name: str = Form("Supermercado"),
    archivo: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    contenido_bytes = await archivo.read()

    # 1. Subir imagen a MinIO
    try:
        image_url = subir_ticket_imagen(contenido_bytes, archivo.filename)
    except Exception as e:
        print(f"Aviso MinIO desconectado: {e}")
        image_url = f"http://localhost:9000/tickets/{archivo.filename}"

    # 2. Extraer texto mediante OCR unificado
    temp_path = f"./temp_{archivo.filename}"
    with open(temp_path, "wb") as f:
        f.write(contenido_bytes)

    try:
        texto_ocr = procesar_lectura_ticket(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # 3. Guardar en BD
    ticket = PurchaseTicket(
        user_id=user_id,
        refrigerator_id=refrigerator_id,
        store_name=store_name,
        ticket_image_url=image_url,
        raw_text_ocr=texto_ocr,
        processed_by_ai=False
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    # Registrar tambien la imagen en food_images
    imagen_registro = FoodImage(
        ticket_id=ticket.id,
        image_url=image_url,
        image_type="ticket",
        ocr_extracted_text=texto_ocr
    )
    session.add(imagen_registro)
    session.commit()

    return {
        "mensaje": "Ticket subido y texto extraido con exito",
        "ticket_id": ticket.id,
        "image_url": image_url,
        "ocr_preview": texto_ocr[:250]
    }
