# 📋 FLUJO DE NEGOCIO - GENERACIÓN DE ORDEN DE TRANSPORTE (OT)

## 🎯 Objetivo General

Crear un agente conversacional que guíe al usuario a través de un proceso estructurado de 6 fases para generar una Orden de Transporte (OT) de Chilexpress de forma inteligente y sin fricciones.

---

## 📊 VISIÓN GENERAL DEL FLUJO

```
┌─────────────────────────────────────────────────────────────┐
│ USUARIO INICIA CONVERSACIÓN                                 │
│ "Quiero cotizar un envío"                                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ FASE 1: COTIZACIÓN   │ ← API Chilexpress
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │ FASE 2: DATOS REMITENTE      │ ← MongoDB + Chilexpress
        └──────────┬───────────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │ FASE 3: TIPO DE ENTREGA      │ ← Decisión del usuario
        └──────────┬───────────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │ FASE 4: DATOS DESTINATARIO   │ ← APIs de Dirección/Oficinas
        └──────────┬───────────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │ FASE 5: CONFIRMACIÓN         │ ← Validación de datos
        └──────────┬───────────────────┘
                   │
                   ▼
          aca debo preguntar si quiere pago online o en oficina...si es oficina genero OT         
        ┌──────────────────────────────┐
        │ FASE 6: GENERAR OT           │ ← API Chilexpress + QR
        └──────────┬───────────────────┘
                   │
                   ▼
        si es pago online levanto pasarela de pago, confirmo y genero OT

        ┌──────────────────────────────┐
        │ OT GENERADA ✅                │
        │ Usuario recibe QR             │
        └──────────────────────────────┘
```

---

## 🔄 FASE 1: COTIZACIÓN

### Objetivo
Obtener opciones de servicios disponibles con sus precios para la ruta solicitada.

### Flujo de Negocio

#### 1.1 Capturar Información del Envío

**Usuario proporciona** (puede ser en una o varias interacciones):
- Origen (ciudad o localidad)
- Destino (ciudad o localidad)
- Peso del paquete (en kilogramos)
- Dimensiones (largo, ancho, alto en centímetros) - OPCIONAL
- Valor declarado del contenido



**Validaciones en esta etapa**:
- ✅ Origen y destino son ciudades válidas en Chile
- ✅ Peso es un número positivo
- ✅ Valor declarado es un número positivo
-✅ Dimensiones en cm

#### 1.2 Normalizar Datos para API

**Convertir entrada del usuario a formato de API**:

```javascript
// Usuario dice "Santiago", API necesita "STG"
ciudadOrigen = mapearCiudad("Santiago") → "STG"

// Usuario dice "Temuco", API necesita "ZCO"
ciudadDestino = mapearCiudad("Temuco") → "ZCO"

// Usuario dice "2kg"
peso = extraerNumero("2kg") → 2

// Si no proporciona dimensiones, usar defaults
largo = 30
ancho = 20
alto = 10

// Usuario dice "50 mil pesos"
valorDeclarado = extraerNumero("50 mil") → 50000
```

**Mapeo de Ciudades** (CRÍTICO):
```
Santiago     → STG
Maipú        → MAIP
Temuco       → ZCO
Valparaíso   → VAL
Concepción   → CNP
Puerto Montt → PTO
La Serena    → LAS
Iquique      → IQU
Arica        → ARI
Calama       → CAL
```

**IMPORTANTE**: 
- ❌ NO enviar "CL-STG" (con prefijo)
- ✅ SÍ enviar "STG" (sin prefijo)

#### 1.3 Llamar a API de Cotización

**API a usar**:
```
POST https://devservices.wschilexpress.com/agendadigital/api/v4/Cotizador/GetCotizadorNacional

Headers:
  Content-Type: application/json
  Ocp-Apim-Subscription-Key: {API_KEY}

Body:
{
  "ciudadOrigen": "STG",
  "ciudadDestino": "ZCO",
  "peso": 2,
  "largo": 30,
  "ancho": 20,
  "alto": 10,
  "valorDeclarado": 50000
}
```

**Respuesta esperada**:
```json
{
  "cotizacion": [
    {
      "servicio": "EXPRESS",
      "serviceCode": 1,
      "valor": 15000,
      "diasEntrega": 1,
      "descripcion": "Entrega en 24 horas"
    },
    {
      "servicio": "STANDARD",
      "serviceCode": 2,
      "valor": 10000,
      "diasEntrega": 3,
      "descripcion": "Entrega en 3 días hábiles"
    },
    {
      "servicio": "ECONÓMICO",
      "serviceCode": 3,
      "valor": 7000,
      "diasEntrega": 5,
      "descripcion": "Entrega en 5 días hábiles"
    }
  ]
}
```

#### 1.4 Almacenar Datos de Cotización

**Guardar en memoria/contexto del agente**:
```javascript
cotizacionGuardada = {
  ciudadOrigen: "STG",
  ciudadDestino: "ZCO",
  peso: 2,
  largo: 30,
  ancho: 20,
  alto: 10,
  valorDeclarado: 50000,
  opciones: [
    { servicio: "EXPRESS", serviceCode: 1, valor: 15000, dias: 1 },
    { servicio: "STANDARD", serviceCode: 2, valor: 10000, dias: 3 },
    { servicio: "ECONÓMICO", serviceCode: 3, valor: 7000, dias: 5 }
  ]
}
```

#### 1.5 Mostrar Opciones al Usuario

**Presentar en formato clara y amigable**:

```
Agent: "Tenemos 3 opciones de servicio para tu envío de 2kg 
        de Santiago a Temuco:

1️⃣ EXPRESS - $15.000 (Entrega en 24 horas)
2️⃣ STANDARD - $10.000 (Entrega en 3 días hábiles)
3️⃣ ECONÓMICO - $7.000 (Entrega en 5 días hábiles)

¿Cuál servicio prefieres?"
```

#### 1.6 Usuario Selecciona Servicio

**Usuario selecciona una opción**:
```
User: "Quiero el Express" 
o
User: "La opción 1"
o
User: "1" (simplemente el número)
```

**Validar y guardar selección**:
```javascript
servicioSeleccionado = {
  servicio: "EXPRESS",
  serviceCode: 1,
  valor: 15000,
  diasEntrega: 1
}
```

### Fin de FASE 1 ✅

El agente ha capturado:
- Ruta del envío (origen, destino)
- Características del paquete (peso, dimensiones)
- Valor declarado
- **Servicio seleccionado con precio**

Se guarda todo en el contexto de la conversación para usar en fases posteriores.

---

## 👤 FASE 2: DATOS DEL REMITENTE

### Objetivo
Obtener y validar los datos de quién envía (remitente). Puede venir de base de datos previa o ser ingresado nuevo.

### Flujo de Negocio

#### 2.1 Solicitar Email del Remitente

**Agent pregunta**:
```
Agent: "Para continuar, necesito tu email para buscar tus datos.
        ¿Cuál es tu correo electrónico?"

User: "s.duarte@hotmail.es"
```

**Validaciones**:
- ✅ Email tiene formato válido (contiene @, .com, etc.)
- ✅ Email no está vacío

#### 2.2 Buscar Datos en Base de Datos Local (MongoDB)

**Flujo**:
```
1. Recibir email del usuario
2. Buscar en MongoDB collection "users" (case-insensitive)
3. Si encuentra → usar datos guardados
4. Si NO encuentra → ir a paso 2.3
```

**Query MongoDB**:
```javascript
db.users.findOne({
  $or: [
    { email: { $regex: "s.duarte@hotmail.es", $options: "i" } },
    { GlsCorreo: { $regex: "S.DUARTE@HOTMAIL.ES", $options: "i" } }
  ]
})
```

**Si ENCUENTRA en MongoDB**:
```json
{
  "email": "s.duarte@hotmail.es",
  "GlsCorreo": "S.DUARTE@HOTMAIL.ES",
  "nombre": "Luis Duarte",
  "rut": "16786170",
  "dv": "9",
  "telefono": "950395840",
  "direccion": "Pasaje Maule",
  "numero": "1471",
  "idCliente": 3400,
  "categoria": "Consolida"
}
```

#### 2.3 Si NO Encontró en MongoDB → Buscar en API Chilexpress

**API a usar**:
```
GET https://devservices.wschilexpress.com/agendadigital/api/v4/user/{email}

Headers:
  Ocp-Apim-Subscription-Key: {API_KEY}
  Origin: https://personas.chilexpress.cl
```

**Respuesta de Chilexpress**:
```json
{
  "User": {
    "IDCliente": 3400,
    "GlsCorreo": "S.DUARTE@HOTMAIL.ES",
    "NomCliente": "Luis",
    "PatCliente": "Duarte",
    "MatCliente": "Cea",
    "NumIdentificacion": "16786170",
    "DvIdentificacion": "9",
    "TelefonoCliente": "950395840",
    "Categoria": {
      "NomCategoria": "Consolida"
    }
  },
  "statusCode": 200
}
```

**Mapear respuesta a formato interno**:
```javascript
remitenteDatos = {
  email: "s.duarte@hotmail.es",
  GlsCorreo: "S.DUARTE@HOTMAIL.ES",
  nombre: "Luis Duarte Cea",  // NomCliente + PatCliente + MatCliente
  rut: "16786170",
  dv: "9",
  telefono: "950395840",
  idCliente: 3400
}
```

#### 2.4 Guardar Datos en MongoDB

**Si vino de Chilexpress, guardar para próximas veces**:
```javascript
db.users.updateOne(
  { email: "s.duarte@hotmail.es" },
  {
    $set: {
      email: "s.duarte@hotmail.es",
      GlsCorreo: "S.DUARTE@HOTMAIL.ES",
      nombre: "Luis Duarte Cea",
      rut: "16786170",
      dv: "9",
      telefono: "950395840",
      idCliente: 3400,
      updatedAt: new Date()
    }
  },
  { upsert: true }
)
```

#### 2.5 Obtener Destinatarios Previos del Usuario

**Mientras se tienen los datos del remitente, obtener destinatarios previos**:

**API a usar**:
```
GET https://devservices.wschilexpress.com/agendadigital/api/v4/destinatario/{email}/cobertura/TODOS/tipoentrega/0

Headers:
  Ocp-Apim-Subscription-Key: {API_KEY}
```

**Respuesta**:
```json
{
  "destinatarios": [
    {
      "nombre": "Constanza Gomez",
      "telefono": "12345678",
      "email": "constanza@gmail.com",
      "direccion": "Avenida Brasil",
      "numero": "7882",
      "ciudad": "Maipú",
      "rut": "16987456"
    },
    {
      "nombre": "Juan Perez",
      "telefono": "98765432",
      "email": "juan@gmail.com",
      "direccion": "Pasaje España",
      "numero": "123",
      "ciudad": "Santiago",
      "rut": "19582485"
    }
  ]
}
```

#### 2.6 Mostrar Datos del Remitente

**Agent presenta los datos encontrados**:

```
Agent: "Encontré tus datos:

👤 Remitente:
   Nombre: Luis Duarte Cea
   RUT: 16786170-9
   Email: s.duarte@hotmail.es
   Teléfono: 950395840

¿Usamos estos datos para el envío?

1️⃣ Sí, usar estos datos
2️⃣ No, ingresar datos nuevos"
```

#### 2.7 Usuario Confirma o Niega

**Opción A: Usuario dice "Sí"**
```
Ir a FASE 2B (Destinatarios Previos)
```

**Opción B: Usuario dice "No, ingresar datos nuevos"**
```
Agent solicita cada dato:
- Nombre completo
- RUT (formato: XXXXXXXX-X)
- Teléfono
- Dirección
- Número de casa

Validar y guardar en MongoDB
```

### 2B: MOSTRAR DESTINATARIOS PREVIOS (Proactivo)

**Si usuario confirmó sus datos, mostrar destinatarios previos**:

```
Agent: "También veo que has enviado a estos destinatarios anteriormente:

1️⃣ Constanza Gomez - Avenida Brasil 7882, Maipú
   Teléfono: 12345678

2️⃣ Juan Perez - Pasaje España 123, Santiago
   Teléfono: 98765432

¿Deseas usar uno de estos o ingresamos un destinatario nuevo?

1️⃣ Usar Constanza Gomez
2️⃣ Usar Juan Perez
3️⃣ Ingresaar nuevo destinatario"
```

**Si usuario selecciona destinatario previo**:
```
Guardar: destinatarioSeleccionado = Constanza Gomez
Ir a FASE 3
```

**Si usuario dice "nuevo destinatario"**:
```
Ir a FASE 3
```

### Fin de FASE 2 ✅

El agente ha capturado:
- **Datos completos del remitente**
- **Email validado**
- **Destinatarios previos mostrados** (proactivo)

Se almacena todo en el contexto para fases posteriores.

---

## 🚚 FASE 3: TIPO DE ENTREGA

### Objetivo
Determinar si el usuario desea entrega a domicilio o retiro en sucursal Chilexpress.

### Flujo de Negocio

#### 3.1 Presentar Opciones de Entrega

**Agent pregunta**:
```
Agent: "¿Cómo deseas recibir el envío?

1️⃣ A domicilio (se entrega en la dirección proporcionada)
2️⃣ Retiro en sucursal (entrega en oficina Chilexpress más cercana)

¿Cuál prefieres?"
```

#### 3.2 Usuario Selecciona

**Usuario elige una opción**:
```
User: "A domicilio" o "1"
o
User: "Retiro en sucursal" o "2"
```

#### 3.3 Guardar Decisión

```javascript
tipoEntrega = usuario.selecciona === "1" ? "DOMICILIO" : "SUCURSAL"

// Para API Chilexpress:
// 1 = Sucursal
// 2 = Domicilio
tipoEntregaCode = usuario.selecciona === "1" ? 2 : 1
```

### Fin de FASE 3 ✅

Se ha capturado:
- **Tipo de entrega**: DOMICILIO o SUCURSAL

La siguiente fase (FASE 4) dependerá de esta selección.

---

## 📍 FASE 4A: DATOS DESTINATARIO - SI SELECCIONÓ DOMICILIO

### Objetivo
Capturar y validar la dirección de entrega.

### Flujo de Negocio

#### 4A.1 Solicitar Dirección

**Agent pregunta**:
```
Agent: "¿A qué dirección quieres que se entregue el envío?

Ejemplo: Avenida Brasil 7882, Maipú

(Proporciona: Calle, número y comuna)"

User: "Avenida Brasil 7882"
```

#### 4A.2 Solicitar Comuna

```
Agent: "¿En qué comuna es?

Ejemplos: Santiago, Maipú, Ñuñoa, Providencia..."

User: "Maipú"
```

#### 4A.3 Validar Dirección

**API a usar** (Validate Address):
```
POST https://devservices.wschilexpress.com/georeference/api/v1.0/address/validate

Body:
{
  "comuna": "Maipú",
  "calle": "Avenida Brasil",
  "numero": "7882"
}
```

**Respuesta si es válida**:
```json
{
  "isValid": true,
  "direccion": "Avenida Brasil 7882, Maipú",
  "latitud": "-33.40118",
  "longitud": "-70.51442"
}
```

**Si NO es válida**:
```json
{
  "isValid": false,
  "error": "Dirección no encontrada en nuestra base de datos"
}
```

**En caso de error**:
```
Agent: "No encontré esa dirección. Por favor, verifica:
        - El nombre de la calle
        - El número
        - La comuna

        ¿Podrías intentar de nuevo?"
```

#### 4A.4 Guardar Coordenadas

**Si dirección fue validada correctamente**:
```javascript
coordenadaDestino = {
  latitud: "-33.40118",
  longitud: "-70.51442"
}
```

#### 4A.5 Solicitar Datos Destinatario

**Agent pregunta**:
```
Agent: "Ahora necesito los datos de quién recibirá el envío:

1. ¿Nombre de la persona que recibe?"

User: "Constanza Gomez"

Agent: "¿RUT? (formato: 12345678-9)"

User: "16987456-9"

Agent: "¿Email?"

User: "constanza@gmail.com"

Agent: "¿Teléfono?"

User: "912345678"
```

#### 4A.6 Validar Datos

```javascript
// Validar RUT
rut = normalizarRUT("16987456-9") → { rut: "16987456", dv: "9" }

// Validar email
email = "constanza@gmail.com" → ✅ formato válido

// Validar teléfono
telefono = "912345678" → ✅ es número
```

#### 4A.7 Guardar en Contexto

```javascript
destinatario = {
  nombre: "Constanza Gomez",
  rut: "16987456",
  dv: "9",
  email: "constanza@gmail.com",
  telefono: "912345678",
  direccion: "Avenida Brasil",
  numero: "7882",
  comuna: "Maipú",
  latitud: "-33.40118",
  longitud: "-70.51442",
  tipoEntrega: 2  // Domicilio
}
```

**Ir a FASE 5 (Confirmación)**

---

## 📍 FASE 4B: DATOS DESTINATARIO - SI SELECCIONÓ SUCURSAL

### Objetivo
Permitir que el usuario seleccione una sucursal Chilexpress y validar datos básicos.

### Flujo de Negocio

#### 4B.1 Solicitar Comuna de Destino

**Agent pregunta**:
```
Agent: "¿En qué comuna quieres retirar el envío?

Ejemplos: Santiago, Maipú, Ñuñoa..."

User: "Santiago"
```

#### 4B.2 Buscar Sucursales en la Comuna

**API a usar**:
```
GET https://devservices.wschilexpress.com/georeference/v2.1/api/v2.0/offices/Internal?comuna=Santiago

Headers:
  Ocp-Apim-Subscription-Key: {API_KEY}
```

**Respuesta**:
```json
{
  "offices": [
    {
      "id": "500",
      "nombre": "ORVIETTO EXPRESS",
      "direccion": "Avenida Libertador O'Higgins 1230",
      "telefono": "2 2550 1234",
      "horarios": "Lunes-Viernes 9:00-18:00, Sábado 9:00-13:00",
      "latitud": "-33.43728",
      "longitud": "-70.66560"
    },
    {
      "id": "742",
      "nombre": "PICK UP MULTISERVICIOS RENCA",
      "direccion": "Pasaje Maule 1471",
      "telefono": "2 2283 4242",
      "horarios": "Lunes-Viernes 9:00-18:00",
      "latitud": "-33.40118",
      "longitud": "-70.51442"
    }
  ]
}
```

#### 4B.3 Mostrar Opciones de Sucursales

**Agent presenta lista**:
```
Agent: "Encontré estas sucursales en Santiago:

1️⃣ ORVIETTO EXPRESS
   Avenida Libertador O'Higgins 1230
   Teléfono: 2 2550 1234
   Horarios: Lunes-Viernes 9:00-18:00, Sábado 9:00-13:00

2️⃣ PICK UP MULTISERVICIOS RENCA
   Pasaje Maule 1471
   Teléfono: 2 2283 4242
   Horarios: Lunes-Viernes 9:00-18:00

¿Cuál prefieres?"
```

#### 4B.4 Usuario Selecciona Sucursal

```
User: "Quiero el Orvietto" o "1"
```

#### 4B.5 Guardar Datos de Oficina

```javascript
sucursalSeleccionada = {
  id: "500",
  nombre: "ORVIETTO EXPRESS",
  direccion: "Avenida Libertador O'Higgins 1230",
  telefono: "2 2550 1234",
  latitud: "-33.43728",
  longitud: "-70.66560"
}
```

#### 4B.6 Solicitar Datos del Receptor en Sucursal

**Agent pregunta**:
```
Agent: "¿Quién recibe el envío en la sucursal?
        (Es para identificación)"

User: "Constanza Gomez"

Agent: "¿RUT de la persona?"

User: "16987456-9"

Agent: "¿Teléfono?"

User: "912345678"
```

#### 4B.7 Guardar en Contexto

```javascript
destinatario = {
  nombre: "Constanza Gomez",
  rut: "16987456",
  dv: "9",
  telefono: "912345678",
  tipoEntrega: 1,  // Sucursal
  codigoOficina: "500",
  nombreOficina: "ORVIETTO EXPRESS",
  direccionOficina: "Avenida Libertador O'Higgins 1230",
  latitud: "-33.43728",
  longitud: "-70.66560"
}
```

**Ir a FASE 5 (Confirmación)**

---

## ✅ FASE 5: CONFIRMACIÓN

### Objetivo
Mostrar resumen completo y pedir confirmación antes de generar la OT.

### Flujo de Negocio

#### 5.1 Preparar Resumen

```javascript
resumen = {
  servicio: "EXPRESS",
  precio: 15000,
  
  remitente: {
    nombre: "Luis Duarte Cea",
    rut: "16786170-9",
    email: "s.duarte@hotmail.es",
    telefono: "950395840"
  },
  
  paquete: {
    peso: 2,
    origen: "Santiago",
    destino: "Temuco"
  },
  
  destinatario: {
    nombre: "Constanza Gomez",
    rut: "16987456-9",
    entrega: "Domicilio",
    direccion: "Avenida Brasil 7882, Maipú"
    // o si es sucursal:
    // entrega: "Sucursal",
    // sucursal: "ORVIETTO EXPRESS"
  }
}
```

#### 5.2 Mostrar Resumen al Usuario

**Agent presenta**:
```
Agent: "Perfecto, aquí está el resumen de tu envío:

📦 PAQUETE:
   Servicio: EXPRESS
   Precio: $15.000
   Ruta: Santiago → Temuco
   Peso: 2 kg

👤 REMITENTE:
   Luis Duarte Cea
   RUT: 16786170-9
   s.duarte@hotmail.es

📍 DESTINATARIO:
   Constanza Gomez (RUT: 16987456-9)
   Domicilio: Avenida Brasil 7882, Maipú

¿Es correcto todo?

1️⃣ Sí, generar orden de transporte
2️⃣ No, necesito cambiar algo"
```

#### 5.3 Usuario Confirma

**Opción A: Usuario dice "Sí"**
```
Agent guarda confirmación
Ir a FASE 6 (Generar OT)
```

**Opción B: Usuario dice "No"**
```
Agent pregunta: "¿Qué necesitas cambiar?"

Usuario puede:
- Cambiar servicio (volver a FASE 1)
- Cambiar datos remitente (volver a FASE 2)
- Cambiar tipo entrega (volver a FASE 3)
- Cambiar datos destinatario (volver a FASE 4)

Se reinicia desde ahí
```

### Fin de FASE 5 ✅

El usuario ha confirmado:
- **Todos los datos son correctos**
- **Está listo para generar la OT**

---

## 🎯 FASE 6: GENERAR ORDEN DE TRANSPORTE

### Objetivo
Generar la OT en el sistema de Chilexpress y obtener el código QR.

### Flujo de Negocio

#### 6.1 Preparar Datos para API

**Mapear datos del contexto a formato de Chilexpress**:

```javascript
otData = {
  // Datos fijos (por defecto)
  NUM_TCC: "123456",
  NRO_GUIA: "0",
  COD_ORIGEN_OT: "CL",
  COD_CONTENIDO: "02",
  
  // Datos de origen y destino (SIN prefijo CL-)
  COD_COBERTURA_ORIGEN: "STG",      // Santiago
  COD_COBERTURA: "ZCO",              // Temuco
  
  // Servicio seleccionado
  SERVICIO_CODE: 1,                   // EXPRESS
  
  // Tipo de entrega
  TIPO_ENTREGA: 2,                    // 1=Sucursal, 2=Domicilio
  
  // DATOS REMITENTE
  NOMBRE_REMITENTE: "Luis Duarte Cea",
  RUT_REMITENTE: "16786170",          // SIN DV
  DV_REMITENTE: "9",
  EMAIL_REMITENTE: "s.duarte@hotmail.es",
  TELEFONO_REMITENTE: "950395840",
  
  // DATOS DESTINATARIO
  NOMBRE_DESTINATARIO: "Constanza Gomez",
  RUT_DESTINATARIO: "16987456",       // SIN DV
  DV_DESTINATARIO: "9",
  EMAIL_DESTINATARIO: "constanza@gmail.com",
  TELEFONO_DESTINATARIO: "912345678",
  
  // DIRECCIÓN DESTINATARIO (si domicilio)
  CALLE_DESTINATARIO: "Avenida Brasil",
  NUMERO_DESTINATARIO: "7882",
  COMUNA_DESTINATARIO: "Maipú",
  LAT_DIR: "-33.40118",               // Solo si TIPO_ENTREGA=2
  LON_DIR: "-70.51442",               // Solo si TIPO_ENTREGA=2
  
  // PAQUETE
  PESO: 2,
  LARGO: 30,
  ANCHO: 20,
  ALTO: 10,
  
  // VALOR
  VALOR_DECLARADO: 50000,
  VALOR_COBERTURA_EXTENDIDA: 0
}
```

#### 6.2 Llamar API para Generar OT

**API a usar**:
```
POST https://devservices.wschilexpress.com/agendadigital/api/v4/prechequeo/PostGenerarOT

Headers:
  Content-Type: application/json
  Ocp-Apim-Subscription-Key: {API_KEY}

Body: {otData}
```

**Respuesta si es exitosa**:
```json
{
  "GeneraOT": {
    "numero_ot": "OT20241023001234",
    "fecha_creacion": "2024-10-23",
    "estado": "ACEPTADA"
  },
  "Respuesta": {
    "resultado": true,
    "respuesta": "OT generada exitosamente"
  }
}
```

**Si hay error**:
```json
{
  "GeneraOT": null,
  "Respuesta": {
    "resultado": false,
    "respuesta": "SIN SERVICIO"
  }
}
```

**Posibles errores**:
- `"SIN SERVICIO"` → Códigos de ciudad incorrectos
- `"Faltan datos obligatorios"` → Datos vacíos o mal formateados
- `"Dirección no válida"` → Coordenadas fuera de rango

#### 6.3 Guardar Número de OT

```javascript
numeroOT = "OT20241023001234"
```

#### 6.4 Obtener Código QR

**API a usar**:
```
GET https://devservices.wschilexpress.com/agendadigital/api/v4/prechequeo/GetCodigoQR?numeroOT=OT20241023001234

Headers:
  Ocp-Apim-Subscription-Key: {API_KEY}
```

**Respuesta**:
```json
{
  "qrCode": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "format": "Base64 PNG",
  "numero_ot": "OT20241023001234"
}
```

#### 6.5 Guardar en Base de Datos

**Guardar OT generada en MongoDB**:
```javascript
db.orders.insertOne({
  numero_ot: "OT20241023001234",
  remitente_email: "s.duarte@hotmail.es",
  remitente: {
    nombre: "Luis Duarte Cea",
    rut: "16786170-9",
    telefono: "950395840"
  },
  destinatario: {
    nombre: "Constanza Gomez",
    rut: "16987456-9",
    telefono: "912345678"
  },
  servicio: "EXPRESS",
  precio: 15000,
  peso: 2,
  origen: "STG",
  destino: "ZCO",
  tipo_entrega: 2,
  createdAt: new Date(),
  estado: "GENERADA",
  qr_code: "base64_data..."
})
```

#### 6.6 Mostrar Éxito al Usuario

**Agent presenta resultado**:
```
Agent: "✅ ¡Orden de Transporte generada exitosamente!

📌 Número de OT: OT20241023001234

👤 Remitente: Luis Duarte Cea
📍 Destino: Temuco
💰 Precio: $15.000
⏱️ Tiempo: Entrega en 24 horas (EXPRESS)

[Aquí va la imagen del QR]

Este QR contiene toda la información de tu envío.
Puedes compartirlo con el destinatario o imprimirlo.

¿Necesitas algo más?"
```

### Fin de FASE 6 ✅

**¡OT GENERADA EXITOSAMENTE!**

El usuario tiene:
- ✅ Número de OT
- ✅ Código QR
- ✅ Confirmación del envío

---

## 🔄 FLUJO COMPLETO - RESUMEN VISUAL

```
┌─────────────────────────────────────────────────────────────┐
│ USUARIO: "Quiero cotizar"                                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
    ┌──────────────▼──────────────┐
    │ FASE 1: COTIZACIÓN          │
    │ ✓ Origen, destino, peso     │
    │ ✓ API Chilexpress           │
    │ ✓ Mostrar opciones de precio│
    │ ✓ Usuario selecciona        │
    └──────────────┬──────────────┘
                   │
    ┌──────────────▼──────────────────────┐
    │ FASE 2: DATOS REMITENTE             │
    │ ✓ Email                              │
    │ ✓ Buscar en MongoDB                 │
    │ ✓ Si no, buscar en Chilexpress      │
    │ ✓ Guardar en MongoDB                │
    │ ✓ Mostrar destinatarios previos     │
    └──────────────┬──────────────────────┘
                   │
    ┌──────────────▼──────────────┐
    │ FASE 3: TIPO ENTREGA        │
    │ ✓ Domicilio o Sucursal      │
    │ ✓ Usuario elige             │
    └──────────────┬──────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
   ┌─────────────────┐  ┌──────────────────────┐
   │ FASE 4A:        │  │ FASE 4B:             │
   │ DOMICILIO       │  │ SUCURSAL             │
   │ ✓ Dirección     │  │ ✓ Elegir sucursal    │
   │ ✓ Validar       │  │ ✓ Mostrar opciones   │
   │ ✓ Coordenadas   │  │ ✓ Usuario selecciona │
   │ ✓ Datos recep.  │  │ ✓ Datos receptores   │
   └────────┬────────┘  └──────────┬───────────┘
            │                      │
            └──────────┬───────────┘
                       │
    ┌──────────────────▼───────────────────┐
    │ FASE 5: CONFIRMACIÓN                 │
    │ ✓ Mostrar resumen completo           │
    │ ✓ Usuario confirma o cambiar         │
    └──────────────┬──────────────────────┘
                   │
    ┌──────────────▼──────────────────────┐
    │ FASE 6: GENERAR OT                   │
    │ ✓ Preparar datos                     │
    │ ✓ API Chilexpress PostGenerarOT      │
    │ ✓ Obtener número OT                  │
    │ ✓ API GetCodigoQR                    │
    │ ✓ Guardar en MongoDB                 │
    │ ✓ Mostrar QR al usuario              │
    └──────────────┬──────────────────────┘
                   │
    ┌──────────────▼──────────────┐
    │ ✅ OT GENERADA              │
    │ Número: OT20241023001234    │
    │ QR: [imagen]                │
    └─────────────────────────────┘
```

---

## 💾 DATOS ALMACENADOS EN CADA FASE

### FASE 1
```
{
  ciudadOrigen: "STG",
  ciudadDestino: "ZCO",
  peso: 2,
  dimensiones: { largo: 30, ancho: 20, alto: 10 },
  valorDeclarado: 50000,
  servicioSeleccionado: { code: 1, nombre: "EXPRESS", valor: 15000 }
}
```

### FASE 2
```
{
  ...fase1,
  remitente: {
    nombre: "Luis Duarte Cea",
    rut: "16786170",
    dv: "9",
    email: "s.duarte@hotmail.es",
    telefono: "950395840",
    idCliente: 3400
  },
  destinatariosPrevios: [...]
}
```

### FASE 3
```
{
  ...fase2,
  tipoEntrega: 2  // 1=Sucursal, 2=Domicilio
}
```

### FASE 4
```
{
  ...fase3,
  destinatario: {
    nombre: "Constanza Gomez",
    rut: "16987456",
    dv: "9",
    email: "constanza@gmail.com",
    telefono: "912345678",
    
    // Si domicilio:
    direccion: "Avenida Brasil",
    numero: "7882",
    comuna: "Maipú",
    latitud: "-33.40118",
    longitud: "-70.51442",
    
    // Si sucursal:
    codigoOficina: "500",
    nombreOficina: "ORVIETTO EXPRESS"
  }
}
```

### FASE 5
```
{
  ...fase4,
  confirmado: true
}
```

### FASE 6
```
{
  ...fase5,
  numeroOT: "OT20241023001234",
  qrCode: "base64_data...",
  generada: true
}
```

---

## 🔑 PUNTOS CRÍTICOS A RECORDAR

### ✅ DO's (Hacer)
1. **Normalizar ciudades a códigos SIN prefijo** (STG, no CL-STG)
2. **Separar RUT y DV** (16786170 + 9, no 16786170-9)
3. **Email lowercase** (s.duarte@hotmail.es)
4. **Buscar primero en MongoDB** antes de Chilexpress
5. **Validar direcciones** antes de generar OT
6. **Guardar en MongoDB** los datos de Chilexpress
7. **Ser proactivo** mostrando destinatarios previos
8. **Confirmación** antes de generar OT

### ❌ DON'Ts (No hacer)
1. ❌ NO enviar prefijo "CL-" en códigos de ciudad
2. ❌ NO juntar RUT y DV (16786170-9 es display, no para API)
3. ❌ NO usar email uppercase para búsqueda
4. ❌ NO llamar Chilexpress sin antes buscar en MongoDB
5. ❌ NO generar OT sin validar dirección
6. ❌ NO confundir TIPO_ENTREGA (1=Sucursal, 2=Domicilio)
7. ❌ NO olvidar latitud/longitud para domicilio
8. ❌ NO generar OT sin confirmación del usuario

---

## 📞 MANEJO DE ERRORES

### En API Chilexpress

```
Error: "SIN SERVICIO"
Causa: Códigos de ciudad incorrectos
Solución: Verificar formato de ciudadOrigen y ciudadDestino (sin CL-)

Error: "Dirección no encontrada"
Causa: Dirección inválida o no en base de datos Chilexpress
Solución: Pedir usuario que verifique y reingrese

Error: "Faltan datos obligatorios"
Causa: Algún campo vacío o nulo
Solución: Validar todos los campos antes de enviar

Error: "RUT inválido"
Causa: Formato incorrecto de RUT
Solución: Normalizar RUT a formato correcto
```

### En Base de Datos

```
Error: "Usuario no encontrado"
Causa: Email no existe en MongoDB ni Chilexpress
Solución: Solicitar datos nuevos y guardar

Error: "Conexión a MongoDB fallida"
Causa: Base de datos no disponible
Solución: Usar Chilexpress como fallback
```

---

## 📊 MÉTRICAS DE ÉXITO

✅ **OT generada exitosamente**
- Usuario completó todas las 6 fases
- Todos los datos fueron validados
- API de Chilexpress respondió correctamente
- QR fue generado

❌ **OT no generada**
- Usuario abandonó el flujo
- Datos inválidos o incompletos
- API de Chilexpress no disponible
- Error en validación de dirección

---

## 🎯 RESUMEN EJECUTIVO

El flujo de generación de OT es un proceso **lineal y estructurado en 6 fases**:

1. **COTIZACIÓN**: Obtener precio de servicios
2. **REMITENTE**: Validar quién envía
3. **TIPO ENTREGA**: ¿A dónde llega?
4. **DESTINATARIO**: Detalles del que recibe
5. **CONFIRMACIÓN**: Validar todo antes de proceder
6. **GENERAR**: Crear OT y obtener QR

Cada fase **recolecta y valida información**, **guarda en bases de datos** cuando es necesario, y **es proactivo mostrando datos previos** para mejorar la experiencia del usuario.

**Total de APIs usadas**: 9 endpoints Chilexpress + MongoDB + OpenAI

**Tiempo promedio**: 3-5 minutos para completar todo el flujo.

---

**FIN DEL DOCUMENTO**
