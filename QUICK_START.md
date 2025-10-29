# 🚀 Inicio Rápido - Versión Python

## 1️⃣ Preparación (5 minutos)

### Windows
```cmd
# Abrir terminal en el directorio del proyecto
cd C:\Users\tu_usuario\Desktop\dev-OTgenerador\dev-OTgenerador

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### macOS / Linux
```bash
cd ~/Desktop/dev-OTgenerador/dev-OTgenerador
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2️⃣ Configuración (5 minutos)

### Crear archivo `.env`
```bash
cp .env.example .env
```

### Editar `.env` con tus credenciales
Necesitarás:
- `MONGO_URI` - URL de conexión MongoDB
- `WATI_API_URL` - URL de WATI
- `WATI_TOKEN` - Token de autenticación WATI
- `AZURE_OPENAI_ENDPOINT` - Endpoint de Azure OpenAI
- `AZURE_OPENAI_API_KEY` - Clave API OpenAI
- `CHILEXPRESS_API_KEY` - Clave API Chilexpress

## 3️⃣ Instalar FFmpeg (Requerido para audio)

### Windows
```cmd
# Usando Chocolatey (si lo tienes)
choco install ffmpeg

# O descargar desde: https://ffmpeg.org/download.html
```

### macOS
```bash
brew install ffmpeg
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

## 4️⃣ Ejecutar la Aplicación

### Modo Desarrollo
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

### Modo Producción (con Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:3000 app:app
```

## 5️⃣ Exposición Local (ngrok)

### En otra terminal
```bash
ngrok http 3000
```

**Copiar la URL HTTPS** (ejemplo: `https://abc123.ngrok-free.app`)

## 6️⃣ Configurar Webhook en WATI

1. Ve a tu panel de WATI: https://wati.io/
2. Navega a **Webhooks** o **Configuración**
3. Pega tu URL de ngrok + `/webhook/wati`
   ```
   https://abc123.ngrok-free.app/webhook/wati
   ```
4. Guarda la configuración
5. ¡Listo! 🎉

## 📋 Verificación

### Test de conexión
```bash
curl http://localhost:3000/
```

**Respuesta esperada:**
```json
{
  "status": "online",
  "message": "Webhook de WATI está funcionando",
  "timestamp": "2024-10-27T...",
  "environment": "development"
}
```

### Test de WATI
```bash
curl http://localhost:3000/test-connection
```

## 🐛 Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Port already in use"
Cambiar puerto en el código o matar el proceso:
```bash
# En Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# En macOS/Linux
lsof -ti:3000 | xargs kill -9
```

### "MongoDB connection failed"
- Verificar `MONGO_URI` en `.env`
- Verificar que MongoDB está accesible
- Verificar credenciales

### "FFmpeg not found"
```bash
# Verificar que está instalado
ffmpeg -version

# Si no está, instalar según tu SO
```

## 📁 Estructura de Archivos

```
dev-OTgenerador/
├── app.py                    # Servidor Flask
├── config.py                 # Configuración
├── requirements.txt          # Dependencias
├── .env                      # Variables de entorno
├── services/                 # Servicios
│   ├── ai_service.py
│   ├── chilexpress_service.py
│   ├── database_service.py
│   ├── flow_manager.py
│   └── ... (10 archivos)
├── controllers/              # Controladores
│   └── webhook_controller.py
├── logs/                     # Archivos de log
└── CITIES_MAPPING.json      # Mapeo de ciudades
```

## ⚡ Comandos Útiles

### Activar entorno virtual
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Deactivar entorno virtual
```bash
deactivate
```

### Ver logs en tiempo real
```bash
# Windows
type logs\webhook_events.log

# macOS/Linux
tail -f logs/webhook_events.log
```

### Instalar paquete adicional
```bash
pip install nombre_paquete
```

### Actualizar requirements
```bash
pip freeze > requirements.txt
```

## 🌐 URLs Importantes

| URL | Descripción |
|-----|-------------|
| http://localhost:3000/ | Health check |
| http://localhost:3000/webhook/wati | Webhook (POST) |
| http://localhost:3000/test-connection | Test conexión |

## 📝 Flujo de Uso

1. **Usuario envía mensaje en WhatsApp**
   ↓
2. **WATI envía webhook a tu URL**
   ↓
3. **Flask recibe y procesa el mensaje**
   ↓
4. **FlowManager decide acción siguiente**
   ↓
5. **Se consultan APIs (Chilexpress, OpenAI, etc)**
   ↓
6. **Se envía respuesta al usuario via WATI**

## 🎯 Próximos Pasos

1. ✅ Instalar dependencias
2. ✅ Configurar `.env`
3. ✅ Ejecutar la aplicación
4. ✅ Exponer con ngrok
5. ✅ Configurar webhook en WATI
6. ✅ Enviar un mensaje de prueba

## 💡 Consejos

- **Desarrollo**: Usa `python app.py` para ver logs en tiempo real
- **Debugging**: Revisa `logs/webhook_events.log` para ver qué sucedió
- **Variables de entorno**: Cámbialas sin reiniciar (cargan de `.env`)
- **Logs**: Buscaen `logs/` si algo va mal

## 📞 Ayuda Rápida

**¿Dónde verificar problemas?**
1. Consola de Flask → Errores de servidor
2. `logs/webhook_events.log` → Historial de eventos
3. Panel de WATI → Verifica webhook status
4. MongoDB Atlas → Verifica datos guardados

---

**¡Ya estás listo! Envía un mensaje de prueba a tu número de WhatsApp conectado en WATI. 🚀**
