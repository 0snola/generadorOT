# 🚀 Guía de Instalación - OT Generator Python

## ✅ Estado Actual

Tu proyecto **solo contiene código Python 100% funcional**. Se ha eliminado completamente todo el código de Node.js/JavaScript.

---

## 📦 Estructura Actual (SOLO PYTHON)

```
✅ Python Files (11)
   ├── app.py                      (Servidor Flask)
   ├── config.py                   (Configuración)
   └── services/                   (10 servicios)

✅ Controllers (2)
   └── webhook_controller.py

✅ Documentación (4)
   ├── README.md                   (Principal)
   ├── QUICK_START.md
   ├── README_PYTHON.md
   └── CONVERSION_SUMMARY.md

✅ Configuración (2)
   ├── requirements.txt
   └── .gitignore

✅ Datos (2)
   ├── CITIES_MAPPING.json
   └── API_MAPPING.json
```

**❌ ELIMINADO:**
- ❌ Carpeta wati-webhook/ (Node.js)
- ❌ package.json y package-lock.json
- ❌ Todos los archivos .js
- ❌ node_modules/

---

## 🎯 Instalación Paso a Paso

### PASO 1: Crear Entorno Virtual (2 minutos)

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### PASO 2: Instalar Dependencias (3 minutos)

```bash
pip install -r requirements.txt
```

**Qué se instala:**
- Flask 3.0.0 (servidor web)
- PyMongo 4.6.0 (MongoDB)
- requests 2.31.0 (HTTP client)
- python-dotenv 1.0.0 (variables de entorno)
- Gunicorn 21.2.0 (servidor producción)
- Y más librerías necesarias

### PASO 3: Configurar Variables de Entorno (5 minutos)

**Copiar ejemplo:**
```bash
cp .env.example .env
```

**Editar `.env` con tus credenciales:**
```env
# Servidor
PORT=3000
ENVIRONMENT=development

# WATI
WATI_API_URL=https://live-mt-server.wati.io/360246
WATI_TOKEN=tu_token_wati

# MongoDB
MONGO_URI=mongodb+srv://usuario:pass@cluster.mongodb.net/

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com/
AZURE_OPENAI_API_KEY=tu_clave_openai

# Chilexpress
CHILEXPRESS_API_KEY=tu_clave_chilexpress
```

### PASO 4: Instalar FFmpeg (Requerido para Audio)

**Windows (Chocolatey):**
```cmd
choco install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg
```

### PASO 5: Ejecutar la Aplicación

**Desarrollo:**
```bash
python app.py
```

**Output esperado:**
```
🚀 Inicializando aplicación...
✅ Base de datos conectada
✅ Aplicación iniciada en modo: development
🚀 Iniciando servidor en puerto 3000...
```

### PASO 6: Exponer con ngrok (Opcional, para testing)

**En otra terminal:**
```bash
ngrok http 3000
```

**Copiar URL HTTPS y configurar en WATI:**
```
https://tu-url-ngrok.app/webhook/wati
```

---

## ✅ Verificación

### Test 1: Servidor ejecutándose
```bash
curl http://localhost:3000/
```

**Respuesta esperada:**
```json
{
  "status": "online",
  "message": "Webhook de WATI está funcionando"
}
```

### Test 2: Base de datos conectada
Revisa los logs:
```bash
tail -f logs/webhook_events.log
```

---

## 📋 Requisitos Finales

- ✅ Python 3.9+
- ✅ pip
- ✅ ffmpeg
- ✅ MongoDB accesible
- ✅ Credenciales de APIs

---

## 🚀 Producción

```bash
# Instalar Gunicorn (ya está en requirements.txt)
pip install gunicorn

# Ejecutar con Gunicorn
gunicorn -w 4 -b 0.0.0.0:3000 app:app

# Con archivo de configuración
gunicorn -c gunicorn.conf.py app:app
```

---

## 🐛 Solución de Problemas

| Problema | Solución |
|----------|----------|
| "Module not found" | `pip install -r requirements.txt` |
| "Port 3000 in use" | Cambiar PORT en config.py |
| "MongoDB connection error" | Verificar MONGO_URI en .env |
| "FFmpeg not found" | Instalar ffmpeg según tu SO |
| "API error" | Verificar credenciales en .env |

---

## 📁 Archivos Importantes

| Archivo | Propósito |
|---------|-----------|
| **app.py** | Punto de entrada (servidor Flask) |
| **config.py** | Variables de configuración |
| **requirements.txt** | Dependencias Python |
| **services/** | Lógica de negocios |
| **controllers/** | Controladores de HTTP |
| **.env** | Variables de entorno (crear) |
| **logs/** | Archivos de log |

---

## 📞 ¿Necesitas Ayuda?

1. Lee **README.md** para descripción general
2. Lee **QUICK_START.md** para inicio rápido
3. Lee **README_PYTHON.md** para documentación completa
4. Revisa **logs/webhook_events.log** para debugging

---

## 🎉 ¡Listo!

Tu proyecto Python está completamente instalado y listo para:
- ✅ Desarrollo local
- ✅ Testing
- ✅ Despliegue en producción

**¡A disfrutar del bot! 🚀**
