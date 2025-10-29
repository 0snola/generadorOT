import logging
import json
import base64
import requests
from config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY

logger = logging.getLogger(__name__)

class ImageService:
    
    @staticmethod
    async def extract_details_from_image(image_buffer):
        """Extraer detalles de envío de la imagen del paquete usando GPT-4 Vision"""
        try:
            base64_image = base64.b64encode(image_buffer).decode('utf-8')
            
            system_prompt = """
                Eres un asistente logístico experto. Tu objetivo es ayudar a un usuario a generar una etiqueta de envío analizando una foto del paquete que desea enviar.

                Analiza la imagen proporcionada y realiza las siguientes tareas:
                1. Identifica el objeto principal del paquete.
                2. Estima las dimensiones del paquete en centímetros: largo (length), ancho (width), y alto (height).
                3. Estima el peso del paquete en kilogramos: peso (weight).
                4. Deja 'ciudadOrigen' y 'ciudadDestino' como cadenas vacías (se preguntarán por separado).

                Responde SOLO con un único objeto JSON limpio que contenga tus estimaciones. Si no puedes hacer una estimación razonable, devuelve los campos numéricos como 0.

                Respuesta de ejemplo:
                {
                  "ciudadOrigen": "",
                  "ciudadDestino": "",
                  "peso": 1.2,
                  "largo": 35,
                  "ancho": 25,
                  "alto": 15
                }
            """
            
            logger.info("🖼️  Analizando imagen con visión...")
            
            response = requests.post(
                AZURE_OPENAI_ENDPOINT,
                json={
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 300,
                    "response_format": {"type": "json_object"}
                },
                headers={
                    'Content-Type': 'application/json',
                    'api-key': AZURE_OPENAI_API_KEY
                }
            )
            
            response.raise_for_status()
            extracted_data = json.loads(response.json()['choices'][0]['message']['content'])
            
            logger.info(f"✅ Datos extraídos de imagen: {extracted_data}")
            return extracted_data
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo detalles de imagen: {e}")
            return {}

image_service = ImageService()
