import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime
import json
from typing import Dict, Any

def init_firebase():
    """Initialize Firebase with credentials."""
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
    })
    
    try:
        firebase_admin.initialize_app(cred)
    except ValueError:
        # App already initialized
        pass
    
    return firestore.client()

def push_to_firebase(collection: str, data: Dict[str, Any], doc_id: str = None) -> str:
    """Push data to Firebase Firestore.
    
    Args:
        collection: Collection name
        data: Data to store
        doc_id: Optional document ID
    
    Returns:
        Document ID
    """
    db = firestore.client()
    
    # Add timestamp
    data["timestamp"] = datetime.now().isoformat()
    
    # Convert to JSON-serializable format
    data = json.loads(json.dumps(data, default=str))
    
    if doc_id:
        db.collection(collection).document(doc_id).set(data)
        return doc_id
    else:
        doc_ref = db.collection(collection).add(data)
        return doc_ref[1].id 