# 🐍 Generador de Órdenes de Transporte - Versión Python

Conversión completa 100% funcional de Node.js a Python del bot inteligente de WhatsApp para generar órdenes de transporte con Chilexpress.

## 📋 Características Principales

- **Máquina de Estados Inteligente**: Gestión completa del flujo conversacional
- **Procesamiento Multimedia**:
  - 📸 Análisis de imágenes con visión por IA (GPT-4V)
  - 🎤 Transcripción de audio (Whisper de Azure)
- **Persistencia con MongoDB**: Guardado de sesiones y datos de usuario
- **Integración con APIs Externas**:
  - 🚚 API de Chilexpress para cotizaciones y envíos
  - 💬 API de WATI para WhatsApp
  - 🤖 Azure OpenAI para IA cognitiva
- **Arquitectura Asincrónica**: Procesamiento eficiente de múltiples usuarios

## 🏗️ Estructura del Proyecto

```
.
├── app.py                          # Servidor principal Flask
├── config.py                       # Configuración centralizada
├── requirements.txt                # Dependencias Python
├── controllers/
│   └── webhook_controller.py      # Controlador de webhooks de WATI
├── services/
│   ├── database_service.py        # Operaciones con MongoDB
│   ├── wati_service.py            # Integración WATI API
│   ├── ai_service.py              # Integración Azure OpenAI
│   ├── chilexpress_service.py     # Integración API Chilexpress
│   ├── session_manager.py         # Gestión de sesiones de usuario
│   ├── flow_manager.py            # Máquina de estados conversacional
│   ├── audio_service.py           # Transcripción de audio
│   ├── audio_converter_service.py # Conversión opus→mp3
│   ├── image_service.py           # Análisis de imágenes
│   └── media_service.py           # Descarga de archivos
├── CITIES_MAPPING.json            # Mapeo de ciudades de Chile
├── .env                           # Variables de entorno (no incluido)
└── logs/                          # Archivos de log

```

## ⚙️ Instalación y Configuración

### Requisitos Previos

- Python 3.9 o superior
- pip
- MongoDB (local o en la nube)
- ffmpeg (para conversión de audio)

### 1. Instalación

```bash
# Clonar o descargar el proyecto
cd dev-OTgenerador

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar ffmpeg (si no está instalado)
# En Windows (usando chocolatey):
choco install ffmpeg
# En macOS:
brew install ffmpeg
# En Linux:
sudo apt-get install ffmpeg
```

### 2. Configuración de Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# Servidor
PORT=3000
ENVIRONMENT=development

# WATI API
WATI_API_URL=https://live-mt-server.wati.io/360246
WATI_TOKEN=your_wati_bearer_token
WATI_PHONE_ID=your_phone_id
WATI_WEBHOOK_TOKEN=your_webhook_token

# MongoDB
MONGO_URI=mongodb+srv://usuario:contraseña@cluster.mongodb.net/?retryWrites=true&w=majority

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_WHISPER_DEPLOYMENT=https://your-resource.openai.azure.com/deployments/your-deployment-id
AZURE_OPENAI_WHISPER_API_KEY=your_whisper_api_key

# Chilexpress API
CHILEXPRESS_API_KEY=your_chilexpress_api_key
```

### 3. Iniciar la Aplicación

```bash
# Desarrollo
python app.py

# Producción (con gunicorn)
gunicorn -w 4 -b 0.0.0.0:3000 app:app
```

El servidor estará disponible en `http://localhost:3000`

### 4. Exponer con ngrok (Desarrollo)

```bash
# En otra terminal
ngrok http 3000

# Copia la URL HTTPS (ej: https://abcd-1234.ngrok-free.app)
```

### 5. Configurar Webhook en WATI

1. Ve al panel de WATI
2. Navega a "Webhooks"
3. Pega la URL: `https://tu-url.ngrok-free.app/webhook/wati`
4. Guarda la configuración

## 🚀 Flujo Conversacional

### FASE 1: COTIZACIÓN
- Usuario proporciona origen, destino y peso
- Sistema consulta Chilexpress y muestra opciones de servicio

### FASE 2: DATOS DEL REMITENTE
- Sistema busca usuario en MongoDB
- Si no existe, solicita datos y los guarda

### FASE 3: TIPO DE ENTREGA
- Usuario elige entre domicilio o sucursal

### FASE 4: DATOS DEL DESTINATARIO
- **Si domicilio**: Valida dirección y obtiene coordenadas
- **Si sucursal**: Muestra sucursales disponibles

### FASE 5: CONFIRMACIÓN
- Usuario revisa y confirma todos los datos

### FASE 6: GENERACIÓN
- Sistema genera OT en Chilexpress
- Envía código QR al usuario

## 📊 Diferencias principales Node.js ↔ Python

| Aspecto | Node.js | Python |
|--------|---------|--------|
| Framework Web | Express | Flask |
| ORM | MongoDB driver nativo | PyMongo |
| Async | Promises/async-await | asyncio |
| Conversión Audio | fluent-ffmpeg | subprocess + ffmpeg |
| HTTP Client | axios | requests |
| Logs | console/file | logging module |

## 🔧 Servicios principales

### DatabaseService
```python
from services.database_service import DatabaseService

# Conectar a MongoDB
DatabaseService.connect()

# Buscar usuario
user = DatabaseService.find_user_by_email('usuario@gmail.com')

# Guardar usuario
DatabaseService.save_user({'email': 'usuario@gmail.com', 'nombre': 'Juan'})
```

### ChilexpressService
```python
from services.chilexpress_service import chilexpress_service

# Obtener cotización
quote = await chilexpress_service.get_quote(
    ciudad_origen='Santiago',
    ciudad_destino='Temuco',
    peso=2
)

# Buscar sucursales
offices = await chilexpress_service.get_offices_by_city('Santiago')

# Generar OT
ot = await chilexpress_service.generate_ot(ot_data)
```

### AIService
```python
from services.ai_service import ai_service

# Extraer parámetros
params = await ai_service.extract_parameters(
    'Quiero enviar 2kg de Santiago a Temuco',
    ['peso', 'origen', 'destino']
)

# Decidir siguiente acción
action = await ai_service.decide_next_action(
    history=[],
    memory={'ciudadOrigen': 'Santiago'},
    goal='Obtener cotización'
)
```

## 📝 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/webhook/wati` | Webhook de WATI |
| GET | `/test-connection` | Probar conexión |

## 🐛 Logging

Los logs se guardan en `logs/webhook_events.log`:

```
[2024-10-23T15:30:45.123456] Event: webhook_received
Data: {
  "ticketId": "ABC123",
  "waId": "5491234567890",
  "text": "Quiero cotizar"
}
...
```

## 🔐 Variables de Entorno Requeridas

- `MONGO_URI`: Conexión a MongoDB
- `WATI_API_URL`: URL base de WATI
- `WATI_TOKEN`: Token de autorización WATI
- `AZURE_OPENAI_ENDPOINT`: Endpoint de Azure OpenAI
- `AZURE_OPENAI_API_KEY`: API key de OpenAI
- `CHILEXPRESS_API_KEY`: API key de Chilexpress

## 🎯 Funcionalidades Adicionales

- ✅ Transcripción de mensajes de voz
- ✅ Análisis de imágenes de paquetes
- ✅ Búsqueda inteligente de ciudades
- ✅ Validación de direcciones
- ✅ Generación de códigos QR
- ✅ Persistencia de sesiones
- ✅ Historial de conversaciones

## 📞 Soporte

Para problemas o preguntas:
1. Revisa los logs en `logs/webhook_events.log`
2. Verifica las variables de entorno
3. Asegúrate de que MongoDB esté accesible
4. Confirma que las credenciales de APIs sean correctas

## 📜 Licencia

ISC

## ✨ Versión Actualizada

- **Versión Original**: Node.js
- **Versión Python**: 1.0.0 (100% funcional)
- **Convertido**: Octubre 2024

---

**¡Disfruta del bot en Python! 🐍**
