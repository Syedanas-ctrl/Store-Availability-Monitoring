import csv
from datetime import datetime, time
from io import StringIO
import uuid
from app.business_hour.model import BusinessHour, DayOfWeek
from app.models import Store
from app.database import engine
from app.store_status.enum import ActivityStatus
from sqlalchemy.orm import Session
import pytz

def parse_timestamp(timestamp_str):
    for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

def backfill_store_status(csv_path: str, db: Session):
    stores_dict = {store.id: store for store in db.query(Store).all()}
    
    # Prepare data for COPY
    copy_data = []
    new_stores = set()

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for i, row in enumerate(reader, start=1):
            store_id = int(row['store_id'])
            if store_id not in stores_dict:
                new_stores.add(store_id)
            
            timestamp = pytz.utc.localize(parse_timestamp(row['timestamp_utc']))
            current_timestamp = datetime.now(pytz.utc)
            status_id = uuid.uuid4().int & (1<<63)-1
            #status_id, store_id, status, timestamp, created_by, created_at, updated_by, updated_at
            copy_data.append(f"{status_id}\t{store_id}\t{ActivityStatus[row['status'].upper()].value.upper()}\t{timestamp}\tbackfill_script\t{current_timestamp}\tbackfill_script\t{current_timestamp}\n")

            if i % 100000 == 0:
                print(f"Processed {i} rows...")

    print(f"CSV processing complete. Total rows: {i}")
    print(f"Number of new stores found: {len(new_stores)}")

    # Handle new stores
    for store_id in new_stores:
        new_store = Store(
            id=store_id,
            timezone='America/Chicago',
            created_by='missing_store_backfill',
            updated_by='missing_store_backfill'
        )
        db.add(new_store)
        
        for day in DayOfWeek:
            business_hour = BusinessHour(
                store_id=store_id,
                day_of_week=day,
                start_time=pytz.timezone('America/Chicago').localize(datetime.combine(datetime.now().date(), time(0, 0))),
                end_time=pytz.timezone('America/Chicago').localize(datetime.combine(datetime.now().date(), time(23, 59, 59))),
                created_by='missing_store_backfill',
                updated_by='missing_store_backfill'
            )
            db.add(business_hour)
    
    db.commit()

    print("starting bulk insert of store status data...")
    # Use COPY for bulk insert
    conn = engine.raw_connection()
    with conn.cursor() as cur:
        cur.copy_from(
            StringIO(''.join(copy_data)),
            'store_status',
            columns=('id', 'store_id', 'status', 'timestamp', 'created_by', 'created_at', 'updated_by', 'updated_at')
        )
    conn.commit()
    
    print(f"Inserted {len(copy_data)} rows of store status data")

if __name__ == '__main__':
    csv_path = 'app/csv/store_status.csv'
    with Session(engine) as db:
        backfill_store_status(csv_path, db)
    print("Store status backfill completed successfully.")