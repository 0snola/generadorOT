import logging
import subprocess
import io
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioConverterService:
    
    @staticmethod
    async def convert_opus_to_mp3(opus_buffer):
        """Convert opus audio buffer to mp3 using ffmpeg"""
        try:
            logger.info(f"🔊 Convirtiendo audio de {len(opus_buffer)} bytes de opus a mp3...")
            
            # Create temporary files
            opus_temp = Path('/tmp/audio_input.opus')
            mp3_temp = Path('/tmp/audio_output.mp3')
            
            # Write input buffer
            opus_temp.write_bytes(opus_buffer)
            
            # Convert using ffmpeg
            command = [
                'ffmpeg',
                '-i', str(opus_temp),
                '-acodec', 'libmp3lame',
                '-ab', '192k',
                str(mp3_temp)
            ]
            
            result = subprocess.run(command, capture_output=True, text=True)
            
            # Cleanup input
            opus_temp.unlink()
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception("FFmpeg conversion failed")
            
            # Read output
            mp3_buffer = mp3_temp.read_bytes()
            
            # Cleanup output
            mp3_temp.unlink()
            
            logger.info(f"✅ Audio convertido a {len(mp3_buffer)} bytes de mp3")
            return mp3_buffer
            
        except Exception as e:
            logger.error(f"❌ Error convertiendo audio: {e}")
            raise Exception("No se pudo convertir el audio")

audio_converter_service = AudioConverterService()
