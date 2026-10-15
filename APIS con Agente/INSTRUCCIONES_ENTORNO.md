# Guía del Entorno: APIS con Agente

Esta guía contiene los pasos y comandos para activar el entorno virtual, ejecutar la API y poner a prueba los módulos de MinIO, FastMCP y OCR.

---

## 1. Acceso y Activación del Entorno Virtual

Abre tu terminal de PowerShell en la carpeta raíz del proyecto y activa el entorno virtual:

```powershell
cd "c:\Users\bauti\OneDrive\Documentos\classroom\9B\Mike\APIS con Agente"
.\venv\Scripts\Activate.ps1
```

Si estás utilizando la consola de comandos estándar (CMD):

```cmd
cd "c:\Users\bauti\OneDrive\Documentos\classroom\9B\Mike\APIS con Agente"
.\venv\Scripts\activate.bat
```

Para confirmar que estás dentro del entorno correcto:

```powershell
Get-Command python | Select-Object Source
```

---

## 2. Instalación de Dependencias

Una vez activado el entorno, instala todas las librerías necesarias ejecutando:

```powershell
pip install -r requirements.txt
```

O si deseas instalar los paquetes clave de lectura y procesamiento:

```powershell
pip install PyPDF2 ddddocr Pillow easyocr fastmcp boto3 sqlmodel fastapi uvicorn requests python-multipart
```

---

## 3. Iniciar el Servidor de APIs (FastAPI)

Para levantar el backend con recarga automática y acceso a la documentación interactiva de Swagger:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

* **Documentación interactiva Swagger:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Documentación alternativa Redoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 4. Sembrar Datos Iniciales (Usuario y Refrigerador Demo)

Para poder vincular tickets y alimentos, ejecuta una petición al endpoint demo o hazlo desde la interfaz Swagger:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/refrigerators/seed-demo" -Method POST
```

Esto creará automáticamente el registro del usuario base y el refrigerador inteligente asociado a tu ESP32.

---

## 5. Probar el Servidor FastMCP y la Lectura OCR

Puedes probar directamente la herramienta de extracción de tickets pasando la ruta de una imagen o Base64:

```powershell
python .\app\tools\ocr_fastmcp.py "ruta_a_tu_ticket.jpg"
```

O iniciar el servidor MCP para que los agentes LLM puedan utilizarlo como herramienta:

```powershell
python .\app\tools\ocr_fastmcp.py
```

---

## 6. Comandos en Terminal para Probar Subida y Ver las URLs de MinIO

Para ejecutar todo el ciclo en un solo paso, puedes correr el script automático que te preparé:

```powershell
.\probar_flujo_completo.ps1
```

O si prefieres ejecutar los comandos paso a paso en tu terminal de PowerShell:

### Paso A: Subir el ticket y obtener su URL de MinIO en tiempo real

```powershell
# 1. Obtener los IDs demo del usuario y del refrigerador
$demo = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/refrigerators/seed-demo" -Method Post

# 2. Subir imagen a la API mediante curl (compatible con todas las versiones de PowerShell)
$rutaTicket = "C:\Users\bauti\Downloads\Mercadona-2025A-captura_400900.jpg"
$jsonRaw = & curl.exe -s -F "user_id=$($demo.user_id)" -F "refrigerator_id=$($demo.refrigerator_id)" -F "store_name=Mercadona" -F "archivo=@$rutaTicket" http://127.0.0.1:8000/api/v1/tickets/upload
$respuesta = $jsonRaw | ConvertFrom-Json

# 3. Mostrar en pantalla la URL generada en MinIO y el ID
Write-Host "URL en MinIO: " $respuesta.image_url
Write-Host "Ticket ID:    " $respuesta.ticket_id
Write-Host "Texto OCR:    " $respuesta.ocr_preview
```

### Paso B: Consultar en terminal todos los tickets registrados y sus URLs de MinIO

Para listar todos los tickets que se han guardado con sus enlaces a MinIO en formato tabla:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/tickets/" -Method Get | Format-Table id, store_name, ticket_image_url, created_at
```

### Paso C: Consultar el detalle de un ticket específico

```powershell
$ticketId = $respuesta.ticket_id
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/tickets/$ticketId" -Method Get | Format-List *
```

---

## 7. Cómo Acceder y Navegar en la Interfaz Web de MinIO

MinIO ofrece dos puertos de funcionamiento:
* **Puerto 9000 (API S3):** Para comunicación de backend y generación de enlaces de descarga directa
* **Puerto 9001 (Consola Web):** Interfaz visual gráfica interactiva para el navegador

### Paso 1: Iniciar el contenedor de MinIO con Docker
Abre Docker Desktop o ejecuta en tu terminal directamente en esta carpeta:

```powershell
cd "c:\Users\bauti\OneDrive\Documentos\classroom\9B\Mike\APIS con Agente"
docker-compose up -d
```

### Paso 2: Abrir la consola web en el navegador
Ingresa en tu navegador a la siguiente dirección:
[http://localhost:9001](http://localhost:9001)

### Paso 3: Iniciar sesión con las credenciales
* **Usuario:** `admin`
* **Contraseña:** `passwordseguro123`

### Paso 4: Navegar y ver los tickets almacenados
* En la barra lateral izquierda haz clic en **Buckets**
* Selecciona el bucket **tickets**
* Dentro verás el explorador de archivos (**Object Browser**) con las imágenes subidas
* Al hacer clic sobre cualquier archivo (por ejemplo `Mercadona-2025A-captura_400900.jpg`) podrás previsualizar la imagen del ticket, descargarla o copiar su URL directa

---

## 8. Configuración del ESP32 y Red WiFi

Tu entorno de red actual se compone de:
* **Red WiFi de la PC:** `5B_5G` (Banda 5 GHz con IP local `192.168.0.100`)
* **Red WiFi del ESP32:** `5B` (Banda 2.4 GHz del mismo módem con contraseña `18988932`)
* **Módem / Router común:** `192.168.0.1` (BSSID `24:2f:d0:f0:d3:6e`)
* **Puerto COM del ESP32:** `COM8` a `115200` baudios

Ambos dispositivos comparten la misma red local `192.168.0.x`, por lo que se pueden comunicar por HTTP y MQTT sin restricciones.

---

## 9. Operación del Sistema: Comando Único o Desglose Manual

Tienes dos formas de trabajar con el sistema: mediante un único comando automático que levanta todo a la vez, o levantando cada terminal de forma individual.

---

### Opción A: Comando Único de Activación con Pestañas (Recomendado)

Para no tener que abrir terminales a mano ni escribir comandos repetitivos, el lanzador automático `iniciar_todo.ps1` detecta tu Windows Terminal (`wt.exe`) y abre automáticamente cada servicio en una pestaña dedicada dentro de la misma ventana:

```powershell
cd "c:\Users\bauti\OneDrive\Documentos\classroom\9B\Mike\APIS con Agente"
.\iniciar_todo.ps1
```

Este comando ejecuta de una sola vez:
1. Levanta los contenedores de MinIO y PostgreSQL en segundo plano
2. Abre automáticamente una pestaña para el servidor FastAPI (`uvicorn main:app --reload`)
3. Abre automáticamente una pestaña para el **Agente Inteligente de Discord** (`python discord_agent.py`)
4. Abre automáticamente una pestaña de consola con el entorno virtual listo para que envíes comandos o pruebas

---

### Opción B: Desglose Individual de Comandos por Terminal o Pestaña

Si deseas tener control manual completo, puedes abrir cuatro pestañas en Windows Terminal y ejecutar en cada una:

#### Terminal 1: Almacenamiento MinIO y Base de Datos (Docker)
Inicia los servicios dentro de tu carpeta `APIS con Agente`:
```powershell
cd "c:\Users\bauti\OneDrive\Documentos\classroom\9B\Mike\APIS con Agente"
docker-compose up -d
```
* Consola gráfica de MinIO: [http://localhost:9001](http://localhost:9001) (admin / passwordseguro123)

#### Terminal 2: Servidor Backend FastAPI
Levanta la API que gestiona los refrigeradores, tickets y llamadas OCR:
```powershell
cd "c:\Users\bauti\OneDrive\Documentos\classroom\9B\Mike\APIS con Agente"
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
* Documentación interactiva de APIs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

#### Terminal 3: Agente Inteligente de Discord
Inicia el bot que recibe fotos de tickets, analiza con OCR y extrae alimentos con la IA:
```powershell
cd "c:\Users\bauti\OneDrive\Documentos\classroom\9B\Mike\APIS con Agente"
.\venv\Scripts\Activate.ps1
python discord_agent.py
```
* Escucha eventos de Discord, lee adjuntos de tickets y notifica al ESP32 por `COM8`

#### Terminal 4: Cliente para Pruebas Manuales
Aquí interactúas con los servicios enviando imágenes y consultando los registros:

1. **Activar el entorno:**
   ```powershell
   cd "c:\Users\bauti\OneDrive\Documentos\classroom\9B\Mike\APIS con Agente"
   .\venv\Scripts\Activate.ps1
   ```

2. **Obtener usuario y refrigerador destino (Sembrado):**
   ```powershell
   $demo = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/refrigerators/seed-demo" -Method Post
   ```
   #### 1. Usuario Demo
   * **Nombre:** `Usuario Demo`
   * **Correo electrónico:** `demo@refrigerador.local`
   * **Contraseña (hash):** `hash_demo_123`
   * **Teléfono:** `555-1234`
   * **ID (UUID):** `8b1d1e8c-2365-4bae-81e0-836b7dfdf3e2`
   #### 2. Refrigerador Demo
   * **Nombre:** `Refri Inteligente Cocina`
   * **Marca:** `Samsung / ESP32-S3`
   * **Dispositivo ESP32 vinculado:** `esp32-claw-E54539`
   * **Capacidad:** `400` litros
   * **ID (UUID):** `bb67e873-0e5c-4c5f-8a5e-93dde821f230`
   * **Propietario:** Vinculado directamente al `user_id` del usuario anterior

3. **Enviar la imagen del ticket a MinIO y extraer su texto con OCR:**
   ```powershell
   $rutaTicket = "C:\Users\bauti\Downloads\Mercadona-2025A-captura_400900.jpg"
   curl.exe -s -F "user_id=$($demo.user_id)" -F "refrigerator_id=$($demo.refrigerator_id)" -F "store_name=Mercadona" -F "archivo=@$rutaTicket" http://127.0.0.1:8000/api/v1/tickets/upload
   ```

4. **Consultar todos los tickets registrados con su URL de MinIO:**
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/tickets/" -Method Get | Format-Table id, store_name, ticket_image_url, created_at
   ```


