import logging
import requests
import io
from config import AZURE_OPENAI_WHISPER_DEPLOYMENT, AZURE_OPENAI_WHISPER_API_KEY

logger = logging.getLogger(__name__)

class AudioService:
    
    @staticmethod
    async def transcribe_audio(audio_buffer):
        """Transcribe audio using Azure Whisper"""
        try:
            logger.info(f"🎤 Transcribiendo audio de {len(audio_buffer)} bytes...")
            
            files = {'file': ('audio.mp3', io.BytesIO(audio_buffer), 'audio/mpeg')}
            
            response = requests.post(
                AZURE_OPENAI_WHISPER_DEPLOYMENT,
                files=files,
                headers={'api-key': AZURE_OPENAI_WHISPER_API_KEY}
            )
            
            response.raise_for_status()
            data = response.json()
            text = data.get('text', '')
            
            logger.info(f"✅ Audio transcrito: {text}")
            return text
            
        except Exception as e:
            logger.error(f"❌ Error transcribiendo audio: {e}")
            raise Exception("No se pudo transcribir el audio")

audio_service = AudioService()
