import logging
from datetime import datetime, timezone
from services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class SessionManager:
    
    @staticmethod
    async def get_session(ticket_id):
        """Get or create session"""
        try:
            session = DatabaseService.get_session(ticket_id)
            if session is None:
                session = SessionManager.create_blank_session(ticket_id)
                DatabaseService.save_session(session)
            return session
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            raise
    
    @staticmethod
    def create_blank_session(ticket_id):
        """Create a blank session"""
        return {
            'ticket_id': ticket_id,
            'wa_id': None,
            'state': 'IDLE',
            'flow_data': {},
            'messages': [],
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
    
    @staticmethod
    async def add_message_to_session(ticket_id, message_data):
        """Add message to session"""
        try:
            session = await SessionManager.get_session(ticket_id)
            session['wa_id'] = message_data.get('waId')
            session['messages'].append(message_data)
            session['updated_at'] = datetime.now(timezone.utc)
            DatabaseService.save_session(session)
            return session
        except Exception as e:
            logger.error(f"Error adding message to session: {e}")
            raise
    
    @staticmethod
    async def update_state(ticket_id, new_state):
        """Update session state"""
        try:
            session = await SessionManager.get_session(ticket_id)
            session['state'] = new_state
            session['updated_at'] = datetime.now(timezone.utc)
            DatabaseService.save_session(session)
            logger.info(f"✅ Updated state for {ticket_id} to {new_state}")
        except Exception as e:
            logger.error(f"Error updating state: {e}")
            raise
    
    @staticmethod
    async def update_flow_data(ticket_id, new_data):
        """Update flow data"""
        try:
            session = await SessionManager.get_session(ticket_id)
            session['flow_data'] = {**session.get('flow_data', {}), **new_data}
            session['updated_at'] = datetime.now(timezone.utc)
            DatabaseService.save_session(session)
            logger.info(f"✅ Updated flowData for {ticket_id}: {session['flow_data']}")
        except Exception as e:
            logger.error(f"Error updating flow data: {e}")
            raise

session_manager = SessionManager()
