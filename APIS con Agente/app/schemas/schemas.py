from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None

class RefrigeratorCreate(BaseModel):
    user_id: str
    name: str
    brand: Optional[str] = None
    esp32_device_id: Optional[str] = None
    capacity_liters: Optional[int] = None

class FoodCreate(BaseModel):
    refrigerator_id: str
    name: str
    category: Optional[str] = "General"
    quantity: float = 1.0
    unit: str = "piezas"
    expiration_date: Optional[date] = None

class TicketUploadResponse(BaseModel):
    mensaje: str
    ticket_id: str
    store_name: Optional[str]
    image_url: str
    ocr_preview: str
