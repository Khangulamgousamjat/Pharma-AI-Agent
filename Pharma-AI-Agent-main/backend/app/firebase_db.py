"""
firebase_db.py — Firebase Admin SDK initialization and dependency.

This module replaces database.py (SQLAlchemy) for the Firestore migration.
"""

import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, firestore, auth

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Firebase Initialization
# ---------------------------------------------------------------------------
db = None

def init_firebase():
    """
    Initialize the Firebase Admin SDK on application startup.
    Safe to call multiple times.
    """
    global db
    if not firebase_admin._apps:
        try:
            # First check for an environment variable mapping (e.g. for Vercel/Render)
            firebase_creds_env = os.environ.get('FIREBASE_CREDENTIALS')
            if firebase_creds_env:
                logger.info("Initializing Firebase from FIREBASE_CREDENTIALS env var.")
                creds_dict = json.loads(firebase_creds_env)
                cred = credentials.Certificate(creds_dict)
            else:
                # Fallback to local file
                key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'firebase_key.json')
                logger.info(f"Initializing Firebase from local key file: {key_path}")
                cred = credentials.Certificate(key_path)
            
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK. Error: {e}")
            raise e
            
    if db is None:
        db = firestore.client()

def get_db():
    """
    FastAPI dependency that provides the Firestore client per request.
    Unlike SQLAlchemy sessions, Firestore client doesn't need to be yielded/closed
    per request, but we keep this function signature for compatibility with routes.
    
    Returns:
        firestore.Client: The initialized Firestore client.
    """
    if db is None:
        init_firebase()
    return db
