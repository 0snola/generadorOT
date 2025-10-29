import logging
import requests
from config import WATI_API_URL, WATI_TOKEN
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class WatiService:
    
    @staticmethod
    async def send_whatsapp_message(phone_number, message_options):
        """Send WhatsApp message via WATI API"""
        try:
            whatsapp_number = phone_number
            
            base_config = {
                'headers': {
                    'Authorization': WATI_TOKEN
                }
            }
            
            url = ''
            params = {}
            data = {}
            
            message_type = message_options.get('type', 'text')
            
            if message_type == 'text':
                url = f"{WATI_API_URL}/api/v1/sendSessionMessage/{whatsapp_number}"
                data = {'messageText': message_options.get('text', '...')}
                base_config['headers']['Content-Type'] = 'application/x-www-form-urlencoded'
                
            elif message_type == 'buttons':
                url = f"{WATI_API_URL}/api/v1/sendInteractiveButtonsMessage"
                params = {'whatsappNumber': whatsapp_number}
                base_config['headers']['Content-Type'] = 'application/json'
                data = {
                    'body': message_options.get('body', 'Selecciona una opción'),
                    'buttons': [
                        {'text': btn.get('text', 'Opción')} 
                        for btn in message_options.get('buttons', [])
                    ]
                }
                
            elif message_type == 'list':
                url = f"{WATI_API_URL}/api/v1/sendInteractiveListMessage"
                params = {'whatsappNumber': whatsapp_number}
                base_config['headers']['Content-Type'] = 'application/json'
                data = {
                    'body': message_options.get('body', 'Selecciona un elemento'),
                    'buttonText': message_options.get('buttonText', 'Seleccionar'),
                    'sections': message_options.get('sections', [])
                }
            else:
                raise ValueError('Tipo de mensaje no soportado')
            
            response = requests.post(
                url,
                params=params,
                json=data if base_config['headers'].get('Content-Type') == 'application/json' else None,
                data=urlencode(data) if base_config['headers'].get('Content-Type') == 'application/x-www-form-urlencoded' else None,
                headers=base_config['headers']
            )
            
            response.raise_for_status()
            logger.info(f"✅ Mensaje enviado exitosamente: {response.json()}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error detallado enviando mensaje: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response data: {e.response.text}")
            raise

async_send_message = WatiService.send_whatsapp_message
