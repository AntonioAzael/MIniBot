from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.models import Refrigerator, User
from app.schemas.schemas import RefrigeratorCreate, UserCreate

router = APIRouter(prefix="/refrigerators", tags=["Refrigerators"])

@router.get("/", response_model=List[Refrigerator])
def listar_refrigeradores(session: Session = Depends(get_session)):
    return session.exec(select(Refrigerator)).all()

@router.post("/", response_model=Refrigerator)
def crear_refrigerador(datos: RefrigeratorCreate, session: Session = Depends(get_session)):
    refrigerador = Refrigerator(
        user_id=datos.user_id,
        name=datos.name,
        brand=datos.brand,
        esp32_device_id=datos.esp32_device_id,
        capacity_liters=datos.capacity_liters
    )
    session.add(refrigerador)
    session.commit()
    session.refresh(refrigerador)
    return refrigerador

@router.post("/seed-demo")
def sembrar_datos_demo(session: Session = Depends(get_session)):
    # Comprobar si ya existe un usuario de prueba
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

    # Comprobar si ya existe un refrigerador
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

    return {
        "mensaje": "Datos demo listos para vincular tickets y alimentos",
        "user_id": user.id,
        "refrigerator_id": refri.id
    }
