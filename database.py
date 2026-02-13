from pymongo import MongoClient
from config import Config
import json
from datetime import datetime


class Database:
    def __init__(self):
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.DB_NAME]
        self.users = self.db.users
        self.sessions = self.db.sessions

    def create_user(self, email, user_id):
        """Create a new user"""
        user = {
            'email': email,
            'user_id': user_id,
            'passkey_credentials': [],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        self.users.insert_one(user)
        return user

    def get_user_by_email(self, email):
        """Get user by email"""
        return self.users.find_one({'email': email})

    def get_user_by_id(self, user_id):
        """Get user by user_id"""
        return self.users.find_one({'user_id': user_id})

    def add_passkey_credential(self, user_id, credential):
        """Add a passkey credential to a user"""
        self.users.update_one(
            {'user_id': user_id},
            {
                '$push': {'passkey_credentials': credential},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )

    def get_user_credentials(self, user_id):
        """Get all passkey credentials for a user"""
        user = self.users.find_one({'user_id': user_id})
        return user.get('passkey_credentials', []) if user else []

    def get_user_and_credential_by_credential_id(self, credential_id):
        """Get user and matching credential by credential ID"""
        user = self.users.find_one(
            {'passkey_credentials.credential_id': credential_id})
        if not user:
            return None, None

        for credential in user.get('passkey_credentials', []):
            if credential.get('credential_id') == credential_id:
                return user, credential

        return None, None

    def update_credential_counter(self, user_id, credential_id, new_counter):
        """Update the signature counter for a credential"""
        self.users.update_one(
            {
                'user_id': user_id,
                'passkey_credentials.credential_id': credential_id
            },
            {
                '$set': {
                    'passkey_credentials.$.sign_count': new_counter,
                    'updated_at': datetime.utcnow()
                }
            }
        )

    def create_session(self, session_id, user_id, saml_request, expires_at):
        """Create a session for tracking SAML authentication flow"""
        session = {
            'session_id': session_id,
            'user_id': user_id,
            'saml_request': saml_request,
            'created_at': datetime.utcnow(),
            'expires_at': expires_at,
            'authenticated': False
        }
        self.sessions.insert_one(session)
        return session

    def get_session(self, session_id):
        """Get a session by ID"""
        return self.sessions.find_one({'session_id': session_id})

    def update_session(self, session_id, authenticated=True):
        """Mark session as authenticated"""
        self.sessions.update_one(
            {'session_id': session_id},
            {'$set': {'authenticated': authenticated}}
        )

    def delete_session(self, session_id):
        """Delete a session"""
        self.sessions.delete_one({'session_id': session_id})

    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        self.sessions.delete_many({'expires_at': {'$lt': datetime.utcnow()}})


# Global database instance
db = Database()
