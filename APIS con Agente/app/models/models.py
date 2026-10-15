import uuid
from typing import Optional, List
from datetime import datetime, timezone, date
from sqlmodel import SQLModel, Field, Relationship

def generar_uuid() -> str:
    return str(uuid.uuid4())

def fecha_actual() -> datetime:
    return datetime.now(timezone.utc)

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(default_factory=generar_uuid, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    password_hash: str
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=fecha_actual)

    refrigerators: List["Refrigerator"] = Relationship(back_populates="user")
    tickets: List["PurchaseTicket"] = Relationship(back_populates="user")

class Refrigerator(SQLModel, table=True):
    __tablename__ = "refrigerators"
    id: str = Field(default_factory=generar_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    name: str
    brand: Optional[str] = None
    esp32_device_id: Optional[str] = None
    capacity_liters: Optional[int] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=fecha_actual)

    user: Optional[User] = Relationship(back_populates="refrigerators")
    foods: List["Food"] = Relationship(back_populates="refrigerator")
    tickets: List["PurchaseTicket"] = Relationship(back_populates="refrigerator")

class Food(SQLModel, table=True):
    __tablename__ = "foods"
    id: str = Field(default_factory=generar_uuid, primary_key=True)
    refrigerator_id: str = Field(foreign_key="refrigerators.id")
    name: str = Field(index=True)
    category: Optional[str] = None
    quantity: float = Field(default=1.0)
    unit: str = Field(default="piezas")
    purchase_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: str = Field(default="fresco")
    created_at: datetime = Field(default_factory=fecha_actual)
    consumed_at: Optional[datetime] = None

    refrigerator: Optional[Refrigerator] = Relationship(back_populates="foods")
    images: List["FoodImage"] = Relationship(back_populates="food")

class PurchaseTicket(SQLModel, table=True):
    __tablename__ = "purchase_tickets"
    id: str = Field(default_factory=generar_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    refrigerator_id: str = Field(foreign_key="refrigerators.id")
    store_name: Optional[str] = None
    purchase_date: Optional[date] = None
    ticket_image_url: Optional[str] = None
    raw_text_ocr: Optional[str] = None
    processed_by_ai: bool = Field(default=False)
    created_at: datetime = Field(default_factory=fecha_actual)

    user: Optional[User] = Relationship(back_populates="tickets")
    refrigerator: Optional[Refrigerator] = Relationship(back_populates="tickets")
    food_images: List["FoodImage"] = Relationship(back_populates="ticket")

class FoodImage(SQLModel, table=True):
    __tablename__ = "food_images"
    id: str = Field(default_factory=generar_uuid, primary_key=True)
    food_id: Optional[str] = Field(default=None, foreign_key="foods.id")
    ticket_id: Optional[str] = Field(default=None, foreign_key="purchase_tickets.id")
    image_url: str
    image_type: str = Field(default="ticket")
    ocr_extracted_text: Optional[str] = None
    ai_analysis: Optional[str] = None

    food: Optional[Food] = Relationship(back_populates="images")
    ticket: Optional[PurchaseTicket] = Relationship(back_populates="food_images")

class Sensor(SQLModel, table=True):
    __tablename__ = "sensors"
    id: str = Field(default_factory=generar_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    refrigerator_id: str = Field(foreign_key="refrigerators.id")
    sensor_type: str
    name: str
    esp32_pin: Optional[str] = None
    mqtt_topic: Optional[str] = None
    is_active: bool = Field(default=True)
    last_reading_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=fecha_actual)

class SensorReading(SQLModel, table=True):
    __tablename__ = "sensor_readings"
    id: str = Field(default_factory=generar_uuid, primary_key=True)
    sensor_id: str = Field(foreign_key="sensors.id")
    value: float
    unit: str
    threshold_alert: bool = Field(default=False)
    alert_message: Optional[str] = None
    recorded_at: datetime = Field(default_factory=fecha_actual)

class Camera(SQLModel, table=True):
    __tablename__ = "cameras"
    id: str = Field(default_factory=generar_uuid, primary_key=True)
    sensor_id: Optional[str] = None
    user_id: str = Field(foreign_key="users.id")
    ip_address: Optional[str] = None
    rtsp_url: Optional[str] = None
    is_recording: bool = Field(default=False)
    storage_path: Optional[str] = None
    created_at: datetime = Field(default_factory=fecha_actual)

class CameraEvent(SQLModel, table=True):
    __tablename__ = "camera_events"
    id: str = Field(default_factory=generar_uuid, primary_key=True)
    camera_id: str = Field(foreign_key="cameras.id")
    event_type: str
    snapshot_url: Optional[str] = None
    ai_description: Optional[str] = None
    severity: str = Field(default="info")
    detected_at: datetime = Field(default_factory=fecha_actual)
    acknowledged: bool = Field(default=False)

class Location(SQLModel, table=True):
    __tablename__ = "locations"
    id: str = Field(default_factory=generar_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    label: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    geofence_radius_m: Optional[int] = None
    is_primary: bool = Field(default=False)

class EmergencyContact(SQLModel, table=True):
    __tablename__ = "emergency_contacts"
    id: str = Field(default_factory=generar_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    location_id: Optional[str] = Field(default=None, foreign_key="locations.id")
    name: str
    relationship: Optional[str] = None
    phone_primary: str
    phone_secondary: Optional[str] = None
    priority: int = Field(default=1)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=fecha_actual)

class AIChatLog(SQLModel, table=True):
    __tablename__ = "ai_chat_logs"
    id: str = Field(default_factory=generar_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    refrigerator_id: Optional[str] = Field(default=None, foreign_key="refrigerators.id")
    role: str
    message: str
    attached_image_url: Optional[str] = None
    ai_action_taken: Optional[str] = None
    tokens_used: int = Field(default=0)
    created_at: datetime = Field(default_factory=fecha_actual)
