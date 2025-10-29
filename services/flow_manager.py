import logging
import asyncio
from config import STATES
from services.session_manager import SessionManager
from services.ai_service import ai_service
from services.chilexpress_service import chilexpress_service
from services.wati_service import WatiService
from services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class FlowManager:
    
    @staticmethod
    async def handle_message(session, message_data):
        """Manejar mensaje entrante y administrar el flujo de conversación"""
        try:
            ticket_id = session.get('ticket_id')
            wa_id = session.get('wa_id')
            user_text = (message_data.get('text') or '').lower()
            
            # Mensaje de bienvenida
            is_first_message = len(session.get('messages', [])) <= 1
            if (is_first_message or 'hola' in user_text) and session['state'] != STATES['GATHERING_SENDER_DATA']:
                await WatiService.send_whatsapp_message(wa_id, {
                    'type': 'text',
                    'text': '👋 ¡Hola! Soy Emilia, tu asistente virtual de Chilexpress 👩🏻‍💼\nPara cotizar tu envío dime las dimensiones de tu paquete, por ejemplo: 40x20x10. O, si prefieres, envíame una foto de tu paquete y yo estimaré las dimensiones por ti.'
                })
                await SessionManager.update_state(ticket_id, STATES['GATHERING_QUOTE_DATA'])
                return
            
            # State machine
            state = session.get('state', STATES['IDLE'])
            
            if state == STATES['GATHERING_QUOTE_DATA']:
                await FlowManager.handle_quote_gathering(ticket_id, session, message_data)
            elif state == STATES['CONFIRMING_QUOTE_DATA']:
                await FlowManager.handle_quote_confirmation(ticket_id, session, user_text)
            elif state == STATES['QUOTATION_RESULTS_SHOWN']:
                await FlowManager.handle_service_selection(ticket_id, session, message_data)
            elif state == STATES['GATHERING_SENDER_DATA']:
                await FlowManager.handle_sender_data(ticket_id, session, message_data)
            elif state == STATES['CONFIRMING_SENDER_DATA']:
                await FlowManager.handle_sender_confirmation(ticket_id, session, user_text)
            elif state == STATES['GATHERING_RECIPIENT_DATA']:
                await FlowManager.handle_recipient_data(ticket_id, session, message_data)
            elif state == STATES['CONFIRMING_RECIPIENT_DATA']:
                await FlowManager.handle_recipient_confirmation(ticket_id, session, user_text)
            elif state == STATES['CHOOSING_DELIVERY_TYPE']:
                await FlowManager.handle_delivery_choice(ticket_id, session, user_text)
            elif state == STATES['GETTING_DELIVERY_ADDRESS']:
                await FlowManager.handle_address(ticket_id, session, message_data)
            elif state == STATES['SELECTING_OFFICE']:
                await FlowManager.handle_office_selection(ticket_id, session, message_data)
            elif state == STATES['CONFIRMING_DELIVERY_DETAILS']:
                await FlowManager.handle_delivery_confirmation(ticket_id, session, user_text)
            elif state == STATES['AWAITING_PAYMENT_METHOD']:
                await FlowManager.handle_payment_method(ticket_id, session, user_text)
            elif state == STATES['FINAL_CONFIRMATION']:
                await FlowManager.handle_final_confirmation(ticket_id, session, user_text)
            else:
                await FlowManager.handle_general_ai(ticket_id, session)
                
        except Exception as e:
            logger.error(f"Error manejando mensaje: {e}")
    
    @staticmethod
    async def handle_quote_gathering(ticket_id, session, message_data):
        """Manejar recopilación de datos de cotización"""
        wa_id = session.get('wa_id')
        memory = session.get('flow_data', {})
        last_question = memory.get('last_question', '')
        
        # Extract parameters
        fields = ['ciudadOrigen', 'ciudadDestino', 'peso', 'largo', 'ancho', 'alto', 'valorDeclarado']
        extracted_params = await ai_service.extract_parameters(message_data.get('text'), fields, last_question)
        memory = {**memory, **extracted_params}
        await SessionManager.update_flow_data(ticket_id, memory)
        
        # Check if we have weight (dimensiones), then ask for valor declarado
        if memory.get('peso') and not memory.get('valorDeclarado'):
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': '¡Excelente! He calculado las medidas. Ahora, ¿cuál es el valor declarado de tu paquete? (Por ejemplo: 45500 pesos)'
            })
            await SessionManager.update_flow_data(ticket_id, {'last_question': 'valor_declarado'})
            return
        
        # Check if we have enough data for quotation
        if memory.get('ciudadOrigen') and memory.get('ciudadDestino') and memory.get('peso') and memory.get('valorDeclarado'):
            # Show summary before requesting quotation
            summary = f"""Listo 😊 ya tengo los datos de tu envío:
Tipo de envío: Encomienda nacional
Tamaño: {memory.get('largo', 30)} × {memory.get('ancho', 20)} × {memory.get('alto', 10)} cm
Peso: {memory.get('peso')} kg
Valor declarado: ${memory.get('valorDeclarado'):,.0f}

¿Están correctos o deseas editar algo?"""
            
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'buttons',
                'body': summary,
                'buttons': [{'text': 'Sí'}, {'text': 'Editar'}]
            })
            await SessionManager.update_state(ticket_id, STATES['CONFIRMING_QUOTE_DATA'])
            return
        
        # Ask for missing data
        question = ""
        if not memory.get('ciudadOrigen'):
            question = "¿Desde qué comuna realizas el envío?"
        elif not memory.get('ciudadDestino'):
            question = f"OK, origen {memory.get('ciudadOrigen')}. ¿A qué comuna de destino lo envías?"
        elif not memory.get('peso'):
            question = "¡Genial! Ahora necesito las dimensiones. Puedes escribirlas (ej: '2kg y 40x30x20') o enviar una foto."
        
        if question:
            await WatiService.send_whatsapp_message(wa_id, {'type': 'text', 'text': question})
            await SessionManager.update_flow_data(ticket_id, {'last_question': question})
    
    @staticmethod
    async def handle_quote_confirmation(ticket_id, session, user_text):
        """Manejar confirmación de datos de cotización"""
        wa_id = session.get('wa_id')
        flow_data = session.get('flow_data', {})
        
        if 'sí' in user_text or 'correcto' in user_text or 'ok' in user_text or 'está bien' in user_text:
            # Proceed with getting origin and destination
            await SessionManager.update_state(ticket_id, STATES['GATHERING_QUOTE_DATA'])
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': 'Ahora necesito saber la comuna de origen y destino al cual enviarás tu envío. Por ejemplo: "de san miguel a valparaiso"'
            })
        else:
            # Reset and ask to re-enter data
            await SessionManager.update_flow_data(ticket_id, {'peso': None, 'largo': None, 'ancho': None, 'alto': None, 'valorDeclarado': None})
            await SessionManager.update_state(ticket_id, STATES['GATHERING_QUOTE_DATA'])
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': 'Entendido. Volvamos al inicio. ¿Cuál es el peso y las dimensiones de tu paquete? Puedes escribirlo o enviar una foto.'
            })
    
    @staticmethod
    async def handle_service_selection(ticket_id, session, message_data):
        """Manejar selección de servicio desde la lista de cotizaciones"""
        wa_id = session.get('wa_id')
        flow_data = session.get('flow_data', {})
        
        if message_data.get('listReply'):
            selected_service = {
                'title': message_data['listReply'].get('title'),
                'id': message_data['listReply'].get('id')
            }
            await SessionManager.update_flow_data(ticket_id, {'selected_service': selected_service})
            
            # Move to sender data gathering
            await SessionManager.update_state(ticket_id, STATES['GATHERING_SENDER_DATA'])
            await FlowManager.handle_sender_data(ticket_id, session, message_data)
        else:
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': 'Por favor, selecciona un servicio de la lista para continuar.'
            })
    
    @staticmethod
    async def handle_sender_data(ticket_id, session, message_data):
        """Manejar recopilación de datos del remitente"""
        wa_id = session.get('wa_id')
        flow_data = session.get('flow_data', {})
        
        # Check for existing user
        if not flow_data.get('sender'):
            existing_user = DatabaseService.find_user_by_phone(wa_id)
            if existing_user:
                confirmation_msg = f"""Hemos encontrado tus datos:
Nombre: {existing_user.get('nombre')}
RUT: {existing_user.get('rut')}
Email: {existing_user.get('email')}
Teléfono: {existing_user.get('phone')}

¿Son correctos?"""
                await WatiService.send_whatsapp_message(wa_id, {
                    'type': 'buttons',
                    'body': confirmation_msg,
                    'buttons': [{'text': 'Sí, continuar'}, {'text': 'No, editar'}]
                })
                await SessionManager.update_flow_data(ticket_id, {'sender': existing_user})
                await SessionManager.update_state(ticket_id, STATES['CONFIRMING_SENDER_DATA'])
                return
        
        # Extract sender data
        fields = ['nombre', 'rut', 'email', 'telefono']
        extracted_params = await ai_service.extract_parameters(message_data.get('text'), fields)
        sender_data = {**flow_data.get('sender', {}), **extracted_params}
        await SessionManager.update_flow_data(ticket_id, {'sender': sender_data})
        
        # Check missing fields
        missing = []
        if not sender_data.get('nombre'): missing.append('nombre')
        if not sender_data.get('rut'): missing.append('RUT')
        if not sender_data.get('email'): missing.append('email')
        if not sender_data.get('telefono'): missing.append('teléfono')
        
        if missing:
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': f"Por favor, indícame tu {', '.join(missing)}."
            })
        else:
            # Save and continue
            await DatabaseService.save_user({'phone': wa_id, **sender_data})
            await SessionManager.update_state(ticket_id, STATES['GATHERING_RECIPIENT_DATA'])
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': '¡Gracias! He guardado tus datos. Ahora, por favor, ingresa los datos del destinatario: Nombre completo, RUT y teléfono.'
            })
    
    @staticmethod
    async def handle_sender_confirmation(ticket_id, session, user_text):
        """Manejar confirmación de datos del remitente"""
        wa_id = session.get('wa_id')
        
        if 'sí' in user_text or 'continuar' in user_text or 'ok' in user_text:
            await SessionManager.update_state(ticket_id, STATES['GATHERING_RECIPIENT_DATA'])
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': 'Ahora necesito que me indiques los datos del destinatario:\n\nNombre completo\nEmail:\nNúmero de teléfono:\n\n💬 Puedes escribirlos, enviarlos por audio o mandarme una imagen.'
            })
        else:
            await SessionManager.update_flow_data(ticket_id, {'sender': {}})
            await SessionManager.update_state(ticket_id, STATES['GATHERING_SENDER_DATA'])
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': 'Entendido. Por favor, ingresa tus datos actualizados: nombre completo, RUT, email y teléfono.'
            })
    
    @staticmethod
    async def handle_recipient_data(ticket_id, session, message_data):
        """Manejar recopilación de datos del destinatario"""
        wa_id = session.get('wa_id')
        flow_data = session.get('flow_data', {})
        
        fields = ['nombre', 'rut', 'telefono', 'email']
        extracted_params = await ai_service.extract_parameters(message_data.get('text'), fields)
        recipient_data = {**flow_data.get('recipient', {}), **extracted_params}
        await SessionManager.update_flow_data(ticket_id, {'recipient': recipient_data})
        
        missing = []
        if not recipient_data.get('nombre'): missing.append('nombre')
        if not recipient_data.get('rut'): missing.append('RUT')
        if not recipient_data.get('telefono'): missing.append('teléfono')
        
        if missing:
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': f"Parece que faltan datos del destinatario. Por favor, indícame su {', '.join(missing)}. 💬 Puedes escribirlos, enviarlos por audio o mandarme una imagen."
            })
        else:
            # Show summary for confirmation
            summary = f"""Perfecto 😊 Ya tengo los datos de destino:
Nombre completo: {recipient_data.get('nombre')}
Email: {recipient_data.get('email', 'No proporcionado')}
Número de teléfono: {recipient_data.get('telefono')}

¿Están correctos o deseas editar algo?"""
            
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'buttons',
                'body': summary,
                'buttons': [{'text': 'Sí'}, {'text': 'Editar'}]
            })
            await SessionManager.update_state(ticket_id, STATES['CONFIRMING_RECIPIENT_DATA'])
    
    @staticmethod
    async def handle_recipient_confirmation(ticket_id, session, user_text):
        """Manejar confirmación de datos del destinatario"""
        wa_id = session.get('wa_id')
        
        if 'sí' in user_text or 'correcto' in user_text or 'ok' in user_text or 'está bien' in user_text:
            await SessionManager.update_state(ticket_id, STATES['CHOOSING_DELIVERY_TYPE'])
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'buttons',
                'body': '¿Cómo quieres realizar la entrega?',
                'buttons': [{'text': 'A domicilio'}, {'text': 'Sucursal Chilexpress'}]
            })
        else:
            await SessionManager.update_flow_data(ticket_id, {'recipient': {}})
            await SessionManager.update_state(ticket_id, STATES['GATHERING_RECIPIENT_DATA'])
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': 'Entendido. Por favor, ingresa de nuevo los datos del destinatario. 💬 Puedes escribirlos, enviarlos por audio o mandarme una imagen.'
            })
    
    @staticmethod
    async def handle_delivery_choice(ticket_id, session, user_text):
        """Manejar elección de tipo de entrega"""
        wa_id = session.get('wa_id')
        flow_data = session.get('flow_data', {})
        ciudad_origen = flow_data.get('ciudadOrigen')
        ciudad_destino = flow_data.get('ciudadDestino')
        
        if not ciudad_destino:
            await SessionManager.update_state(ticket_id, STATES['GATHERING_QUOTE_DATA'])
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': 'Parece que se perdió la información del envío. ¿Podrías indicarme de nuevo el origen y destino?'
            })
            return
        
        if 'domicilio' in user_text:
            await SessionManager.update_state(ticket_id, STATES['GETTING_DELIVERY_ADDRESS'])
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': f"Perfecto, entrega a domicilio en {ciudad_destino}. Por favor, escribe la dirección completa (calle y número)."
            })
        elif 'sucursal' in user_text:
            # Search offices in DESTINO (where customer picks up the package)
            await SessionManager.update_state(ticket_id, STATES['SELECTING_OFFICE'])
            await FlowManager.execute_tool(ticket_id, wa_id, 'get_chilexpress_offices', {'city': ciudad_destino})
        else:
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': 'Por favor, elige una opción válida: "A domicilio" o "Sucursal Chilexpress".'
            })
    
    @staticmethod
    async def handle_address(ticket_id, session, message_data):
        """Manejar entrada de dirección"""
        wa_id = session.get('wa_id')
        flow_data = session.get('flow_data', {})
        ciudad_destino = flow_data.get('ciudadDestino')
        
        address_text = message_data.get('text')
        validation_result = await chilexpress_service.validate_address(address_text, '', ciudad_destino)
        
        if validation_result.get('valid'):
            await SessionManager.update_flow_data(ticket_id, {
                'delivery_address': address_text,
                'address_details': {
                    'lat': validation_result.get('data', {}).get('Latitud'),
                    'lon': validation_result.get('data', {}).get('Longitud')
                }
            })
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': '¡Dirección validada! Estamos listos para el siguiente paso: el pago.'
            })
        else:
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': f"No pudimos validar la dirección en {ciudad_destino}. ¿Puedes verificarla e intentarlo de nuevo?"
            })
    
    @staticmethod
    async def handle_office_selection(ticket_id, session, message_data):
        """Manejar selección de sucursal desde la lista"""
        wa_id = session.get('wa_id')
        
        if message_data.get('listReply'):
            selected_office = {
                'title': message_data['listReply'].get('title'),
                'id': message_data['listReply'].get('id')
            }
            await SessionManager.update_flow_data(ticket_id, {'selected_office': selected_office})
            await SessionManager.update_state(ticket_id, STATES['CONFIRMING_DELIVERY_DETAILS'])
            
            # Show delivery confirmation with buttons
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'buttons',
                'body': f"Has seleccionado: {selected_office.get('title')}. ¿Es correcto?",
                'buttons': [{'text': 'Sí'}, {'text': 'Editar'}]
            })
        else:
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': 'Por favor, selecciona una sucursal de la lista.'
            })
    
    @staticmethod
    async def handle_general_ai(ticket_id, session):
        """Manejar conversación impulsada por IA general"""
        wa_id = session.get('wa_id')
        history = [
            {'role': 'assistant' if msg.get('isOwner') else 'user', 'content': msg.get('text', '')}
            for msg in session.get('messages', [])
        ]
        memory = session.get('flow_data', {})
        goal = f"Continuar con la tarea actual: {session.get('state')}"
        
        decision = await ai_service.decide_next_action(history, memory, goal)
        
        if decision.get('action') == 'ask_question':
            await WatiService.send_whatsapp_message(wa_id, {'type': 'text', 'text': decision.get('question')})
        elif decision.get('action') == 'call_tool':
            await FlowManager.execute_tool(ticket_id, wa_id, decision.get('tool_name'), decision.get('parameters', {}))
        elif decision.get('action') == 'inform_user':
            await WatiService.send_whatsapp_message(wa_id, {'type': 'text', 'text': decision.get('message')})
    
    @staticmethod
    async def execute_tool(ticket_id, wa_id, tool_name, parameters):
        """Ejecutar herramienta basada en el nombre de la herramienta"""
        try:
            if tool_name == 'get_quote':
                quote_params = {
                    'ciudad_origen': parameters.get('ciudadOrigen') or parameters.get('origen'),
                    'ciudad_destino': parameters.get('ciudadDestino') or parameters.get('destino'),
                    'peso': parameters.get('peso'),
                    'valor_declarado': parameters.get('valorDeclarado', 50000),
                    'largo': parameters.get('largo'),
                    'ancho': parameters.get('ancho'),
                    'alto': parameters.get('alto')
                }
                
                if not all([quote_params['ciudad_origen'], quote_params['ciudad_destino'], quote_params['peso']]):
                    await WatiService.send_whatsapp_message(wa_id, {
                        'type': 'text',
                        'text': 'Me falta información clave. Por favor, indica origen, destino y peso.'
                    })
                    return
                
                quote_result = await chilexpress_service.get_quote(**quote_params)
                quote_list = quote_result.get('ListCotiNacional', [])
                
                if quote_list and quote_list[0].get('VALOR'):
                    list_sections = [{
                        'title': 'Servicios de Envío',
                        'rows': [
                            {
                                'id': f"service_{opt.get('COD_SERVICIO')}",
                                'title': opt.get('NOM_SERVICIO', '')[:24],
                                'description': f"${opt.get('VALOR'):,} - {opt.get('GLS_ENTREGA', '')}"[:72]
                            }
                            for opt in quote_list[:10]
                        ]
                    }]
                    
                    await WatiService.send_whatsapp_message(wa_id, {
                        'type': 'list',
                        'body': '¡Listo! Aquí tienes las opciones para tu envío. Por favor, selecciona una:',
                        'buttonText': 'Ver Servicios',
                        'sections': list_sections
                    })
                    await SessionManager.update_state(ticket_id, STATES['QUOTATION_RESULTS_SHOWN'])
                else:
                    await WatiService.send_whatsapp_message(wa_id, {
                        'type': 'text',
                        'text': 'Lo siento, no encontré servicios disponibles. Verifica los datos.'
                    })
                    await SessionManager.update_state(ticket_id, STATES['GATHERING_QUOTE_DATA'])
            
            elif tool_name == 'get_chilexpress_offices':
                city = parameters.get('city')
                offices = await chilexpress_service.get_offices_by_city(city)
                
                if offices:
                    list_sections = [{
                        'title': f"Sucursales en {city}"[:24],
                        'rows': [
                            {
                                'id': f"office_{office.get('officeCode')}",
                                'title': office.get('officeName', '')[:24],
                                'description': f"{office.get('streetName', '')} {office.get('streetNumber', '')}"[:72]
                            }
                            for office in offices[:10]
                        ]
                    }]
                    
                    await WatiService.send_whatsapp_message(wa_id, {
                        'type': 'list',
                        'body': 'Encontré estas sucursales. Por favor, selecciona:',
                        'buttonText': 'Ver Sucursales',
                        'sections': list_sections
                    })
                else:
                    await WatiService.send_whatsapp_message(wa_id, {
                        'type': 'text',
                        'text': f"No encontré sucursales en {city}. ¿Quieres intentar con otra?"
                    })
        
        except Exception as e:
            logger.error(f"Error ejecutando herramienta {tool_name}: {e}")
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': 'Hubo un error procesando tu solicitud. Por favor, intenta de nuevo.'
            })

    @staticmethod
    async def handle_delivery_confirmation(ticket_id, session, user_text):
        """Manejar confirmación de detalles de entrega"""
        wa_id = session.get('wa_id')
        flow_data = session.get('flow_data', {})
        
        if 'sí' in user_text or 'correcto' in user_text or 'ok' in user_text or 'sí' == user_text.lower().strip():
            await SessionManager.update_state(ticket_id, STATES['AWAITING_PAYMENT_METHOD'])
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'buttons',
                'body': '¿Cómo deseas realizar el pago?',
                'buttons': [
                    {'text': 'Pago en Oficina'},
                    {'text': 'Pago en Línea'},
                    {'text': 'Por Pagar en Destino'}
                ]
            })
        else:
            await SessionManager.update_state(ticket_id, STATES['CHOOSING_DELIVERY_TYPE'])
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'buttons',
                'body': 'Entendido. ¿Cómo quieres realizar la entrega?',
                'buttons': [{'text': 'A domicilio'}, {'text': 'Sucursal Chilexpress'}]
            })
    
    @staticmethod
    async def handle_payment_method(ticket_id, session, user_text):
        """Manejar selección de método de pago"""
        wa_id = session.get('wa_id')
        flow_data = session.get('flow_data', {})
        
        payment_method = None
        if 'oficina' in user_text:
            payment_method = 'Pago en Oficina'
        elif 'línea' in user_text or 'online' in user_text:
            payment_method = 'Pago en Línea'
        elif 'destino' in user_text or 'cobro' in user_text:
            payment_method = 'Por Pagar en Destino'
        
        if payment_method:
            await SessionManager.update_flow_data(ticket_id, {'payment_method': payment_method})
            await SessionManager.update_state(ticket_id, STATES['FINAL_CONFIRMATION'])
            await FlowManager.show_final_summary(ticket_id, wa_id, flow_data)
        else:
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': 'Por favor, selecciona un método de pago válido: "Pago en Oficina", "Pago en Línea" o "Por Pagar en Destino".'
            })
    
    @staticmethod
    async def show_final_summary(ticket_id, wa_id, flow_data):
        """Mostrar resumen final antes de confirmar"""
        delivery_type = "Sucursal" if flow_data.get('selected_office') else "Domicilio"
        
        summary = f"""Te dejo el resumen de tu envío:

Origen: {flow_data.get('ciudadOrigen')}
Datos de destino:
Nombre completo: {flow_data.get('recipient', {}).get('nombre')}
Email: {flow_data.get('recipient', {}).get('email', 'No proporcionado')}
Número de teléfono: {flow_data.get('recipient', {}).get('telefono')}"""
        
        if delivery_type == "Domicilio":
            summary += f"\nDirección de destino: {flow_data.get('delivery_address')}"
        else:
            summary += f"\nSucursal: {flow_data.get('selected_office', {}).get('title')}"
        
        summary += f"""
Servicio: {flow_data.get('selected_service', {}).get('title', 'Estándar')}
Total a pagar: ${flow_data.get('quote_total', 'Por confirmar')}
Método de pago: {flow_data.get('payment_method')}

Ya casi terminamos 😊 Presiona "confirmar" para confirmar tu envío."""
        
        await WatiService.send_whatsapp_message(wa_id, {
            'type': 'buttons',
            'body': summary,
            'buttons': [{'text': 'Confirmar'}, {'text': 'Editar'}]
        })
    
    @staticmethod
    async def handle_final_confirmation(ticket_id, session, user_text):
        """Manejar confirmación final antes de generar OT"""
        wa_id = session.get('wa_id')
        flow_data = session.get('flow_data', {})
        
        if 'confirmar' in user_text or 'sí' in user_text or 'ok' in user_text:
            # TODO: Call Chilexpress API to generate OT
            # For now, send confirmation message
            numero_ot = "OT20241028001234"  # Placeholder - should be generated from API
            
            await SessionManager.update_state(ticket_id, STATES['OT_GENERATED'])
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': f"""Tu solicitud se ha realizado con éxito. Aquí tienes la Orden de Transporte (OT) de tu envío.

🚚 OT: {numero_ot}

Debes acercarte a la sucursal seleccionada anteriormente y mostrar este documento"""
            })
        else:
            # Reset to allow editing
            await WatiService.send_whatsapp_message(wa_id, {
                'type': 'text',
                'text': 'Entendido. ¿Qué deseas cambiar? Puedo ayudarte con el origen, destino, datos del destinatario o método de pago.'
            })

flow_manager = FlowManager()
