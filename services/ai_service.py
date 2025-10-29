import logging
import json
import requests
from config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY

logger = logging.getLogger(__name__)

class AIService:
    
    def __init__(self):
        self.endpoint = AZURE_OPENAI_ENDPOINT
        self.api_key = AZURE_OPENAI_API_KEY
    
    async def decide_next_action(self, history, memory, goal):
        """Decidir la siguiente acción basada en el historial de conversación y la memoria"""
        system_prompt = f"""
            Eres un agente cognitivo para Chilexpress en Chile. Tu objetivo es guiar a los usuarios a través de la creación de una orden de envío.
            TODA tu comunicación DEBE ser en español chileno amable y útil.

            EL FLUJO DE PROCESO ES ESTRICTO:
            1.  **COTIZACIÓN**: Obtén una cotización. Recopila parámetros y llama a "get_quote".
            2.  **SELECCIÓN_SERVICIO**: El usuario selecciona un servicio de la cotización.
            3.  **DATOS_REMITENTE**: Obtén los datos del remitente. Pregunta por email, llama a "find_user_by_email". Si no se encuentra, pide todos los detalles.
            4.  **TIPO_ENTREGA**: Después de confirmar los datos del remitente, DEBES pedir al usuario que elija entre "domicilio" (entrega a casa) o "sucursal" (retiro en sucursal).
            5.  **DATOS_DESTINATARIO**:
                - Si "sucursal", DEBES preguntar por la ciudad de destino para buscar oficinas.
                - Si "domicilio", pide la dirección del destinatario y llama a "validate_address".

            REGLAS DE COGNICIÓN:
            1.  **LA MEMORIA ES HECHO**: Los datos en la memoria se consideran un hecho confirmado.
            2.  **USAR LA MEMORIA PARA HERRAMIENTAS**: Cuando una herramienta requiere un parámetro que ya existe en la memoria, úsalo.
            3.  **FLUJO ESTRICTO**: Sigue el flujo de proceso estrictamente.

            Basándote en el contexto, decide la mejor acción única. Responde con un objeto JSON.

            ACCIONES:
            1. {{ "action": "ask_question", "question": "..." }}: Para hacer una pregunta de texto libre.
            2. {{ "action": "ask_with_buttons", "question": "...", "buttons": ["Opción 1", "Opción 2"] }}: Para preguntar con opciones.
            3. {{ "action": "call_tool", "tool_name": "...", "parameters": {{ ... }} }}: Para usar una herramienta.
            4. {{ "action": "inform_user", "message": "..." }}: Para enviar un mensaje.

            Objetivo Actual: {goal}
            Memoria (Datos Recopilados): {json.dumps(memory)}
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            *[{"role": item.get("role", "user"), "content": item.get("content", "")} for item in history]
        ]
        
        try:
            response = requests.post(
                self.endpoint,
                json={
                    "messages": messages,
                    "max_tokens": 300,
                    "temperature": 0.1,
                    "top_p": 1.0,
                    "response_format": {"type": "json_object"}
                },
                headers={
                    "Content-Type": "application/json",
                    "api-key": self.api_key
                }
            )
            
            response.raise_for_status()
            action_json = response.json()['choices'][0]['message']['content']
            logger.info(f"Acción Decidida por IA: {action_json}")
            return json.loads(action_json)
            
        except Exception as e:
            logger.error(f"Error decidiendo próxima acción: {e}")
            return {
                "action": "inform_user",
                "message": "Lo siento, estoy teniendo problemas para procesar tu solicitud."
            }
    
    async def extract_parameters(self, text, fields_to_extract, context_question=""):
        """Extraer parámetros del texto del usuario usando IA"""
        parameters_description = "\n- ".join(fields_to_extract)
        context = f'El usuario acaba de ser preguntado: "{context_question}". Basándote en ese contexto, analiza su respuesta.' if context_question else ""
        
        system_prompt = f"""
            Eres una herramienta de extracción de parámetros.
            {context}
            Tu tarea es analizar el texto del usuario y extraer SOLO los siguientes parámetros:
            - {parameters_description}

            Analiza el siguiente texto: "{text}"

            Responde SOLO con un único objeto JSON limpio que contenga los parámetros que encontraste. Si no encuentras parámetros, devuelve un objeto JSON vacío.
        """
        
        try:
            response = requests.post(
                self.endpoint,
                json={
                    "messages": [{"role": "system", "content": system_prompt}],
                    "max_tokens": 200,
                    "temperature": 0.0,
                    "response_format": {"type": "json_object"}
                },
                headers={
                    "Content-Type": "application/json",
                    "api-key": self.api_key
                }
            )
            
            response.raise_for_status()
            params_json = response.json()['choices'][0]['message']['content']
            logger.info(f"Parámetros Extraídos por IA: {params_json}")
            return json.loads(params_json)
            
        except Exception as e:
            logger.error(f"Error extrayendo parámetros: {e}")
            return {}

ai_service = AIService()
