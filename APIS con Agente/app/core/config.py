import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Smart Refrigerator API")
    environment: str = os.getenv("ENVIRONMENT", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./smart_refrigerator.db")
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    minio_user: str = os.getenv("MINIO_ROOT_USER", "admin")
    minio_password: str = os.getenv("MINIO_ROOT_PASSWORD", "passwordseguro123")
    bucket_tickets: str = os.getenv("MINIO_BUCKET_TICKETS", "tickets")
    bucket_foods: str = os.getenv("MINIO_BUCKET_FOODS", "food-images")
    wifi_ssid: str = os.getenv("WIFI_SSID", "Thrive_Laptops")
    wifi_password: str = os.getenv("WIFI_PASSWORD", "thrive2026")
    esp_port: str = os.getenv("ESP_COM_PORT", "COM8")
    esp_baud: int = int(os.getenv("BAUD_RATE", "115200"))

settings = Settings()
