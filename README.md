# 🐍 OT Generator - Versión Python

Bot inteligente de WhatsApp para generar órdenes de transporte con Chilexpress usando Python, Flask, MongoDB y Azure OpenAI.

## 🚀 Inicio Rápido

### 1. Instalar Dependencias (2 min)
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# o: source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno (3 min)
```bash
# Crear archivo .env basado en .env.example
cp .env.example .env

# Editar .env con tus credenciales:
# - MONGO_URI
# - WATI_API_URL y WATI_TOKEN
# - AZURE_OPENAI_ENDPOINT y AZURE_OPENAI_API_KEY
# - CHILEXPRESS_API_KEY
```

### 3. Ejecutar (1 min)
```bash
python app.py
```

**Esperado:**
```
🚀 Inicializando aplicación...
✅ Base de datos conectada
🚀 Iniciando servidor en puerto 3000...
```

### 4. Exponer Localmente (ngrok)
```bash
ngrok http 3000
# Copiar URL HTTPS y configurar en panel de WATI
```

## 📋 Requisitos Previos

- Python 3.9+
- ffmpeg (para procesamiento de audio)
- MongoDB (local o Atlas)
- Credenciales de: WATI, Azure OpenAI, Chilexpress

## 📚 Documentación

- **QUICK_START.md** - Guía rápida de 10 minutos
- **README_PYTHON.md** - Documentación completa
- **CONVERSION_SUMMARY.md** - Detalles técnicos
- **PROYECTO_CONVERTIDO.md** - Estado del proyecto

## 📁 Estructura

```
.
├── app.py                        # Servidor Flask
├── config.py                     # Configuración
├── requirements.txt              # Dependencias Python
├── services/                     # Servicios
│   ├── ai_service.py            # Azure OpenAI
│   ├── chilexpress_service.py   # APIs Chilexpress
│   ├── database_service.py      # MongoDB
│   ├── flow_manager.py          # Máquina de estados
│   ├── session_manager.py       # Gestión de sesiones
│   ├── wati_service.py          # Integración WATI
│   ├── audio_service.py         # Transcripción
│   ├── audio_converter_service.py  # Conversión audio
│   ├── image_service.py         # Análisis de imágenes
│   └── media_service.py         # Descarga de medios
├── controllers/                  # Controladores
│   └── webhook_controller.py    # Webhooks WATI
├── logs/                        # Archivos de log
└── CITIES_MAPPING.json          # Mapeo de ciudades
```

## 🔧 Configuración

### Variables de Entorno Requeridas
```
PORT=3000
ENVIRONMENT=development
MONGO_URI=mongodb+srv://...
WATI_API_URL=https://live-mt-server.wati.io/...
WATI_TOKEN=tu_token
AZURE_OPENAI_ENDPOINT=https://....openai.azure.com/
AZURE_OPENAI_API_KEY=tu_clave
CHILEXPRESS_API_KEY=tu_clave
```

## 📊 Características

✅ **Máquina de estados inteligente** - Gestión completa del flujo conversacional
✅ **Análisis de imágenes** - Reconocimiento de paquetes con GPT-4V
✅ **Transcripción de audio** - Conversión de voz a texto con Whisper
✅ **Persistencia de sesiones** - MongoDB para almacenamiento duradero
✅ **Integración WATI** - Envío de mensajes por WhatsApp
✅ **APIs Chilexpress** - Cotizaciones, validación y generación de OT
✅ **Logging completo** - Registro detallado de eventos

## 🌐 Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Health check |
| POST | `/webhook/wati` | Webhook de WATI |
| GET | `/test-connection` | Test de conexión |

## 🔐 Seguridad

- ✅ Variables de entorno para credenciales
- ✅ Sin hardcoding de datos sensibles
- ✅ Validación de entrada
- ✅ Manejo seguro de tokens
- ✅ CORS configurado

## 🐛 Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
```

### "MongoDB connection failed"
- Verificar MONGO_URI en .env
- Verificar acceso a MongoDB Atlas
- Verificar credenciales

### "FFmpeg not found"
```bash
# Windows
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

## 📝 Logs

Los logs se guardan en `logs/webhook_events.log`

```bash
# Ver logs en tiempo real
tail -f logs/webhook_events.log
```

## 🚀 Producción

```bash
# Con Gunicorn (4 workers)
gunicorn -w 4 -b 0.0.0.0:3000 app:app

# Con Nginx como reverse proxy
# (Configuración en tu servidor)
```

## 📞 Soporte

1. Revisar `logs/webhook_events.log`
2. Verificar variables de entorno en `.env`
3. Confirmar credenciales de APIs
4. Verificar MongoDB esté accesible

## 📜 Licencia

ISC

---

**Versión:** Python 1.0.0
**Estado:** ✅ Producción Lista
**Compatible:** Python 3.9+

🎉 **¡Disfruta del bot!**

