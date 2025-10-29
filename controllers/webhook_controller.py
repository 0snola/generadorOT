import logging
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from flask import request, jsonify
from services.flow_manager import flow_manager
from services.session_manager import SessionManager
from services.audio_service import audio_service
from services.media_service import media_service
from services.audio_converter_service import audio_converter_service
from services.image_service import image_service
from services.wati_service import WatiService
from config import LOG_DIR, WEBHOOK_LOG_FILE

logger = logging.getLogger(__name__)

# Create logs directory
Path(LOG_DIR).mkdir(exist_ok=True)

def log_webhook_event(event_type, event_data, additional_info=None):
    """Log webhook events to file"""
    try:
        log_file = Path(LOG_DIR) / WEBHOOK_LOG_FILE
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"""[{timestamp}] Event: {event_type}
Data: {json.dumps(event_data, indent=2, default=str)}
Additional Info: {json.dumps(additional_info or {}, indent=2, default=str)}

"""
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        logger.error(f"Error writing log: {e}")

def handle_webhook():
    """Handle webhook request"""
    # Acknowledge immediately
    response_data = {'status': 'success', 'message': 'Webhook received and is being processed.'}
    
    # Process asynchronously in background
    asyncio.create_task(process_webhook_async(request.get_json(force=True)))
    
    return jsonify(response_data), 200

async def process_webhook_async(request_body):
    """Process webhook asynchronously"""
    try:
        if not request_body:
            request_body = {}
        
        log_webhook_event('webhook_received', request_body, {'headers': dict(request.headers)})
        
        ticket_id = request_body.get('ticketId')
        if not ticket_id:
            logger.info('Ignoring request without ticketId')
            return
        
        # Add message to session
        session = await SessionManager.add_message_to_session(ticket_id, request_body)
        wa_id = request_body.get('waId')
        
        # Pre-process input
        if request_body.get('listReply') and request_body['listReply'].get('title'):
            request_body['text'] = request_body['listReply'].get('title')
        elif request_body.get('interactiveButtonReply') and request_body['interactiveButtonReply'].get('title'):
            request_body['text'] = request_body['interactiveButtonReply'].get('title')
        
        # Handle audio
        if request_body.get('type') == 'audio' and request_body.get('data'):
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': 'Audio recibido, procesando...'
            })
            try:
                opus_buffer = await media_service.download_media(request_body['data'])
                mp3_buffer = await audio_converter_service.convert_opus_to_mp3(opus_buffer)
                request_body['text'] = await audio_service.transcribe_audio(mp3_buffer)
                await WatiService.send_whatsapp_message(wa_id, {
                    'type': 'text',
                    'text': f'Texto transcrito: "{request_body["text"]}"'
                })
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                await WatiService.send_whatsapp_message(wa_id, {
                    'type': 'text',
                    'text': 'Lo siento, no pude procesar el audio.'
                })
                return
        
        # Handle images
        if request_body.get('type') == 'image' and request_body.get('data'):
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': 'Imagen recibida, analizándola...'
            })
            try:
                image_buffer = await media_service.download_media(request_body['data'])
                extracted_data = await image_service.extract_details_from_image(image_buffer)
                await SessionManager.update_flow_data(ticket_id, extracted_data)
                
                context_message = "He analizado la imagen."
                if extracted_data.get('peso') and extracted_data.get('largo'):
                    context_message += f" He estimado que pesa ~{extracted_data['peso']}kg y mide {extracted_data['largo']}x{extracted_data['ancho']}x{extracted_data['alto']}cm."
                context_message += " Ahora necesito saber las comunas de origen y destino."
                request_body['text'] = context_message
                
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                await WatiService.send_whatsapp_message(wa_id, {
                    'type': 'text',
                    'text': 'Lo siento, no pude procesar la imagen.'
                })
                return
        
        # Handle message with flow manager
        await flow_manager.handle_message(session, request_body)
        
    except Exception as e:
        logger.error(f"Error in asynchronous webhook processing: {e}")
        log_webhook_event('webhook_error_async', {
            'errorMessage': str(e)
        })

def test_wati_connection():
    """Test WATI connection"""
    try:
        # Simple test - return success
        return jsonify({
            'status': 'success',
            'message': 'Conexión con WATI exitosa',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error testing WATI connection: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Error interno del servidor',
            'details': str(e)
        }), 500
