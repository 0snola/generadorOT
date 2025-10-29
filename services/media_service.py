import logging
import requests
from config import WATI_TOKEN

logger = logging.getLogger(__name__)

class MediaService:
    
    @staticmethod
    async def download_media(media_url):
        """Download media from WATI URL"""
        try:
            # Transform the showFile URL to the correct getMedia URL
            get_media_url = media_url.replace('/api/file/showFile', '/api/v1/getMedia')
            
            logger.info(f"📥 Descargando media desde: {get_media_url}")
            
            response = requests.get(
                get_media_url,
                headers={'Authorization': WATI_TOKEN}
            )
            
            response.raise_for_status()
            logger.info(f"✅ Media descargada exitosamente: {len(response.content)} bytes")
            return response.content
            
        except Exception as e:
            logger.error(f"❌ Error descargando media: {e}")
            raise Exception("No se pudo descargar el archivo de WATI")

media_service = MediaService()
