import logging
import json
import requests
from pathlib import Path
from config import CHILEXPRESS_API_KEY, CHILEXPRESS_BASE_URL, CHILEXPRESS_GEO_BASE_URL

logger = logging.getLogger(__name__)

# Load city mappings
cities_mapping_path = Path(__file__).parent.parent / 'CITIES_MAPPING.json'
with open(cities_mapping_path, 'r', encoding='utf-8') as f:
    city_mappings_data = json.load(f)
    city_mappings = city_mappings_data.get('flatMapping', {})

def map_city_to_code(city_name):
    """Map city name to Chilexpress code"""
    normalized_city = city_name.lower().strip()
    return city_mappings.get(normalized_city, city_name.upper())

class ChilexpressService:
    
    @staticmethod
    async def get_quote(ciudad_origen, ciudad_destino, peso, largo=30, ancho=20, alto=10, valor_declarado=50000):
        """Get quotation from Chilexpress"""
        try:
            params = {
                'CIUDAD_ORIGEN': map_city_to_code(ciudad_origen),
                'CIUDAD_DESTINO': map_city_to_code(ciudad_destino),
                'COD_PRODUCTO': '3',
                'PESO': f"{float(peso):.2f}",
                'LARGO': int(largo),
                'ANCHO': int(ancho),
                'ALTO': int(alto),
                'VALOR_DECLARADO': int(valor_declarado),
                'IND_CLASE_TE': '2',
                'INDTARIFAGENERICA': '0',
                'CANAL_ORIGEN': '8'
            }
            
            logger.info(f"📤 Parámetros de cotización: {params}")
            
            response = requests.get(
                f"{CHILEXPRESS_BASE_URL}/Cotizador/GetCotizadorNacional",
                params=params,
                headers={'Ocp-Apim-Subscription-Key': CHILEXPRESS_API_KEY}
            )
            
            response.raise_for_status()
            logger.info(f"✅ Respuesta de Chilexpress: {response.json()}")
            return response.json()
            
        except Exception as e:
            logger.error(f"❌ Error en cotización: {e}")
            raise Exception("No se pudo obtener la cotización de Chilexpress")
    
    @staticmethod
    async def find_client_by_email(email):
        """Find client by email"""
        try:
            logger.info(f"🔍 Buscando cliente con email: {email}")
            
            response = requests.get(
                f"{CHILEXPRESS_BASE_URL}/cliente/GetCliente",
                params={
                    'TIPO_CLIENTE': 1,
                    'EMAIL': email
                },
                headers={'Ocp-Apim-Subscription-Key': CHILEXPRESS_API_KEY}
            )
            
            if response.status_code in [404, 204]:
                logger.info(f"❌ Cliente no encontrado: {email}")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('CLIENTE'):
                logger.info(f"✅ Cliente encontrado: {data}")
                return data.get('CLIENTE')
            
            logger.info(f"❌ Sin datos de cliente: {email}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error buscando cliente: {e}")
            if hasattr(e, 'response') and e.response and e.response.status_code in [404, 204]:
                return None
            raise
    
    @staticmethod
    async def get_offices_by_city(city):
        """Get offices in a city"""
        try:
            county_name = city.upper().strip()
            logger.info(f"🏢 Buscando sucursales en: {city} ({county_name})")
            
            response = requests.get(
                f"{CHILEXPRESS_GEO_BASE_URL}/offices/Internal",
                params={
                    'countyName': county_name,
                    'type': 0
                },
                headers={'Ocp-Apim-Subscription-Key': CHILEXPRESS_API_KEY}
            )
            
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data.get('offices'), list) and len(data['offices']) > 0:
                logger.info(f"✅ Sucursales encontradas: {len(data['offices'])}")
                return data['offices']
            
            logger.warning(f"⚠️  No offices found: {data}")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo sucursales: {e}")
            raise Exception("No se pudo obtener las sucursales de Chilexpress")
    
    @staticmethod
    async def validate_address(street, number, city):
        """Validate address"""
        try:
            logger.info(f"📍 Validando dirección: {street} {number}, {city}")
            
            response = requests.get(
                f"{CHILEXPRESS_BASE_URL}/direcciones/GetDireccion",
                params={
                    'CodigoCalle': street,
                    'Numero': number,
                    'Comuna': map_city_to_code(city)
                },
                headers={'Ocp-Apim-Subscription-Key': CHILEXPRESS_API_KEY}
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('Latitud') and data.get('Longitud'):
                logger.info(f"✅ Dirección validada: {data}")
                return {'valid': True, 'data': data}
            
            return {'valid': False, 'reason': 'Address not found'}
            
        except Exception as e:
            logger.error(f"❌ Error validando dirección: {e}")
            return {'valid': False, 'reason': 'API error during validation'}
    
    @staticmethod
    async def generate_ot(ot_data):
        """Generate Order of Transport"""
        try:
            logger.info(f"📦 Generando OT con datos: {ot_data}")
            
            response = requests.post(
                f"{CHILEXPRESS_BASE_URL}/prechequeo/PostGenerarOT",
                json=ot_data,
                headers={
                    'Content-Type': 'application/json',
                    'Ocp-Apim-Subscription-Key': CHILEXPRESS_API_KEY
                }
            )
            
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ OT generada: {data}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error generando OT: {e}")
            raise Exception("No se pudo generar la orden de transporte")
    
    @staticmethod
    async def get_qr_code(numero_ot):
        """Get QR code for OT"""
        try:
            logger.info(f"📱 Obteniendo código QR para: {numero_ot}")
            
            response = requests.get(
                f"{CHILEXPRESS_BASE_URL}/prechequeo/GetCodigoQR",
                params={'numeroOT': numero_ot},
                headers={'Ocp-Apim-Subscription-Key': CHILEXPRESS_API_KEY}
            )
            
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ QR obtenido: {data}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo QR: {e}")
            raise Exception("No se pudo obtener el código QR")

chilexpress_service = ChilexpressService()
