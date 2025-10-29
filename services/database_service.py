import logging
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime, timezone
from config import MONGO_URI, MONGO_DB_NAME

logger = logging.getLogger(__name__)

class DatabaseService:
    _instance = None
    _db = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance

    @classmethod
    def connect(cls):
        """Connect to MongoDB database"""
        if cls._db is not None:
            return cls._db
        
        try:
            cls._client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
            cls._db = cls._client[MONGO_DB_NAME]
            cls._db.command('ping')
            logger.info("✅ Successfully connected to MongoDB!")
            return cls._db
        except Exception as e:
            logger.error(f"❌ Could not connect to MongoDB: {e}")
            raise

    @classmethod
    def get_db(cls):
        """Get database instance"""
        if cls._db is None:
            cls.connect()
        return cls._db

    @staticmethod
    def find_user_by_email(email):
        """Find user by email (case-insensitive)"""
        try:
            db = DatabaseService.get_db()
            users = db['users']
            return users.find_one({
                'email': {'$regex': f'^{email}$', '$options': 'i'}
            })
        except Exception as e:
            logger.error(f"Error finding user by email: {e}")
            raise

    @staticmethod
    def find_user_by_phone(phone):
        """Find user by phone number"""
        try:
            db = DatabaseService.get_db()
            users = db['users']
            return users.find_one({'phone': phone})
        except Exception as e:
            logger.error(f"Error finding user by phone: {e}")
            raise

    @staticmethod
    def save_user(user_data):
        """Save or update user"""
        try:
            db = DatabaseService.get_db()
            users = db['users']
            
            # Use phone as primary identifier if available
            identifier = user_data.get('phone') or user_data.get('email')
            if not identifier:
                raise ValueError("User data must contain phone or email")
            
            filter_query = (
                {'phone': user_data['phone']} 
                if user_data.get('phone')
                else {'email': {'$regex': f'^{user_data["email"]}$', '$options': 'i'}}
            )
            
            user_data['updated_at'] = datetime.now(timezone.utc)
            result = users.update_one(filter_query, {'$set': user_data}, upsert=True)
            
            logger.info(f"User saved/updated: matched={result.matched_count}, modified={result.modified_count}")
            return result
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            raise

    @staticmethod
    def get_session(ticket_id):
        """Get session by ticket ID"""
        try:
            db = DatabaseService.get_db()
            sessions = db['sessions']
            return sessions.find_one({'ticket_id': ticket_id})
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            raise

    @staticmethod
    def save_session(session_data):
        """Save or update session"""
        try:
            db = DatabaseService.get_db()
            sessions = db['sessions']
            
            filter_query = {'ticket_id': session_data['ticket_id']}
            session_data['updated_at'] = datetime.now(timezone.utc)
            
            result = sessions.update_one(filter_query, {'$set': session_data}, upsert=True)
            logger.info(f"Session saved: matched={result.matched_count}, modified={result.modified_count}")
            return result
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            raise

    @staticmethod
    def save_order(order_data):
        """Save generated order"""
        try:
            db = DatabaseService.get_db()
            orders = db['orders']
            order_data['created_at'] = datetime.now(timezone.utc)
            result = orders.insert_one(order_data)
            logger.info(f"Order saved with ID: {result.inserted_id}")
            return result
        except Exception as e:
            logger.error(f"Error saving order: {e}")
            raise

    @staticmethod
    def close_connection():
        """Close database connection"""
        if DatabaseService._client:
            DatabaseService._client.close()
            logger.info("Database connection closed")
