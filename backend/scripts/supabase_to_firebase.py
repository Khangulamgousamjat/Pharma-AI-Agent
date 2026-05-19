import os
import sys
import json
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Add the parent directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. INITIALIZE CONNECTIONS
# ---------------------------------------------------------------------------
logger.info("Initializing Supabase (SQLAlchemy) connection...")
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_sql = SessionLocal()

logger.info("Initializing Firebase Admin SDK...")
try:
    # Look for the firebase service account key
    cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), '..', 'firebase_key.json'))
    firebase_admin.initialize_app(cred)
    db_fs = firestore.client()
except Exception as e:
    logger.error(f"Failed to initialize Firebase. Ensure 'firebase_key.json' exists in the backend directory. Error: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# ---------------------------------------------------------------------------
def batch_write(collection_name, data_list, id_field='id'):
    """Write a list of dicts to a Firestore collection in batches of 500."""
    total = len(data_list)
    if total == 0:
        logger.info(f"No records found for {collection_name}.")
        return

    logger.info(f"Migrating {total} records to {collection_name}...")
    batch = db_fs.batch()
    count = 0
    batch_count = 0

    for item in data_list:
        doc_id = str(item.pop(id_field)) # Use original ID as document ID
        doc_ref = db_fs.collection(collection_name).document(doc_id)
        
        # Convert datetime objects to string/timestamp if necessary (Firestore handles Python datetimes)
        batch.set(doc_ref, item)
        count += 1
        
        if count == 500:
            batch.commit()
            batch_count += 500
            logger.info(f"  ... committed {batch_count}/{total} to {collection_name}")
            batch = db_fs.batch()
            count = 0
            
    if count > 0:
        batch.commit()
        batch_count += count
        logger.info(f"  ... committed {batch_count}/{total} to {collection_name}")
        
    logger.info(f"Successfully migrated {collection_name}.")

# ---------------------------------------------------------------------------
# 3. MIGRATION LOGIC
# ---------------------------------------------------------------------------
def migrate_users():
    logger.info("--- MIGRATING USERS ---")
    result = db_sql.execute(text("SELECT * FROM users"))
    users = [dict(row) for row in result.mappings()]
    
    fs_users = []
    for u in users:
        # Don't migrate password hashes if moving to Firebase Auth
        u_data = dict(u)
        u_data.pop('password_hash', None)
        fs_users.append(u_data)
        
    batch_write('users', fs_users)

def migrate_medicines():
    logger.info("--- MIGRATING MEDICINES ---")
    result = db_sql.execute(text("SELECT * FROM medicines"))
    medicines = [dict(row) for row in result.mappings()]
    batch_write('medicines', medicines)

def migrate_orders():
    logger.info("--- MIGRATING ORDERS ---")
    # For orders, we might want to fetch order items and embed them.
    # Assuming there's an 'order_items' table or similar relationship.
    # For this script, we'll migrate the base orders.
    result = db_sql.execute(text("SELECT * FROM orders"))
    orders = [dict(row) for row in result.mappings()]
    
    # Example denormalization: if we had order_items, we would query them here
    # and attach them as a list to the order document.
    
    batch_write('orders', orders)

def migrate_prescriptions():
    logger.info("--- MIGRATING PRESCRIPTIONS ---")
    result = db_sql.execute(text("SELECT * FROM prescriptions"))
    prescriptions = [dict(row) for row in result.mappings()]
    batch_write('prescriptions', prescriptions)

def main():
    try:
        migrate_users()
        migrate_medicines()
        migrate_orders()
        migrate_prescriptions()
        
        logger.info("✅ Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
    finally:
        db_sql.close()

if __name__ == "__main__":
    main()
