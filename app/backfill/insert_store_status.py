import csv
from datetime import datetime, time
from app.business_hour.model import BusinessHour, DayOfWeek
from app.models import Store, StoreStatus
from app.database import engine
from app.store_status.model import Status
from sqlalchemy.orm import Session
import pytz
from multiprocessing import Pool, cpu_count, Manager

def parse_timestamp(timestamp_str, formats):
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

def process_batch(batch, stores_dict):
    records = []
    new_stores = []
    formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']
    for row in batch:
        store_id = int(row['store_id'])
        store = stores_dict.get(store_id)
        if not store:
            new_stores.append(store_id)

        records.append(StoreStatus(
            store_id=store_id,
            status=Status(row['status']),
            timestamp=pytz.utc.localize(parse_timestamp(row['timestamp_utc'], formats)),
            created_by='backfill_script',
            updated_by='backfill_script'
        ))
    return records, new_stores


def insert_records(db, records):
    db.bulk_save_objects(records)
    db.commit()


def backfill_store_status(csv_path: str, db: Session):
    with open(csv_path, mode='r') as file:
        total_rows = sum(1 for row in csv.DictReader(file))

    # Use a Manager to create a shared dictionary
    with Manager() as manager:
        stores_dict = manager.dict()
        stores_dict.update(
            {store.id: store for store in db.query(Store).all()})

        # Create a pool of workers
        pool = Pool(processes=cpu_count())

        batch_size = 10000
        batch = []
        total_records = []

        with open(csv_path, mode='r') as file:
            reader = csv.DictReader(file)
            for index, row in enumerate(reader, start=1):
                batch.append(row)
                if len(batch) == batch_size:
                    # Process batch in parallel
                    batch_result = pool.apply_async(
                        process_batch, (batch, stores_dict))
                    batch_records, new_store_ids = batch_result.get()
                    total_records.extend(batch_records)

                    # Handle new stores
                    for store_id in new_store_ids:
                        if store_id not in stores_dict:
                            new_store = Store(
                                id=store_id,
                                timezone='America/Chicago',
                                created_by='missing_store_backfill',
                                updated_by='missing_store_backfill'
                            )
                            db.add(new_store)
                            db.commit()
                            stores_dict[store_id] = new_store

                            current_date = datetime.now().date()
                            for day in DayOfWeek:
                                business_hour = BusinessHour(
                                    store_id=store_id,
                                    day_of_week=day,
                                    start_time=pytz.timezone('America/Chicago').localize(
                                        datetime.combine(current_date, time.fromisoformat('00:00:00'))),
                                    end_time=pytz.timezone('America/Chicago').localize(
                                        datetime.combine(current_date, time.fromisoformat('23:59:59'))),
                                    created_by='missing_store_backfill',
                                    updated_by='missing_store_backfill'
                                )
                                db.add(business_hour)
                            db.commit()

                    batch = []

                # Batch insert when we have enough records
                if len(total_records) >= 50000:
                    insert_records(db, total_records)
                    total_records = []

                if index % 100000 == 0:
                    print(f"Processed {index} rows",)

        # Process any remaining rows in the last batch
        if batch:
            batch_result = pool.apply_async(
                process_batch, (batch, stores_dict))
            batch_records, _ = batch_result.get()
            total_records.extend(batch_records)

        # Insert any remaining records
        if total_records:
            insert_records(db, total_records)
            print("Inserted remaining records", len(total_records))

        pool.close()
        pool.join()


if __name__ == '__main__':
    csv_path = 'app/csv/store_status.csv'
    with Session(engine) as db:
        backfill_store_status(csv_path, db)
    print("Store status backfill completed successfully.")
