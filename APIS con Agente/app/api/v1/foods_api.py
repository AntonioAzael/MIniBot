from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.models import Food
from app.schemas.schemas import FoodCreate

router = APIRouter(prefix="/foods", tags=["Foods"])

@router.get("/", response_model=List[Food])
def listar_alimentos(session: Session = Depends(get_session)):
    alimentos = session.exec(select(Food)).all()
    return alimentos

@router.get("/{food_id}", response_model=Food)
def obtener_alimento(food_id: str, session: Session = Depends(get_session)):
    alimento = session.get(Food, food_id)
    if not alimento:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")
    return alimento

@router.post("/", response_model=Food)
def registrar_alimento(datos: FoodCreate, session: Session = Depends(get_session)):
    nuevo_alimento = Food(
        refrigerator_id=datos.refrigerator_id,
        name=datos.name,
        category=datos.category,
        quantity=datos.quantity,
        unit=datos.unit,
        expiration_date=datos.expiration_date
    )
    session.add(nuevo_alimento)
    session.commit()
    session.refresh(nuevo_alimento)
    return nuevo_alimento
