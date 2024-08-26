import csv
from datetime import datetime, time
from app.business_hour.model import DayOfWeek
from app.models import BusinessHour, Store
from app.database import engine
from sqlalchemy.orm import Session
import pytz

def backfill_business_hours(csv_path: str, db: Session):
    with open(csv_path, mode='r') as file:
        total_rows = sum(1 for row in csv.DictReader(file))

    # Preload all stores into a dictionary
    stores = {store.id: store for store in db.query(Store).all()}

    batch_size = 1000
    batch = []
    current_date = datetime.now().date()

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for index, row in enumerate(reader, start=1):
            store_id = int(row['store_id'])
            store = stores.get(store_id)

            if not store:
                # Add new store if not found
                store = Store(
                    id=store_id,
                    created_by='missing_store_backfill',
                    updated_by='missing_store_backfill'
                )
                db.add(store)
                db.commit()
                stores[store_id] = store

            tz = pytz.timezone(store.timezone)
            start_time = tz.localize(datetime.combine(current_date, time.fromisoformat(row['start_time_local'] or '00:00:00')))
            end_time = tz.localize(datetime.combine(current_date, time.fromisoformat(row['end_time_local'] or '23:59:59')))

            business_hour = BusinessHour(
                store_id=store_id,
                day_of_week=DayOfWeek(int(row['day'])),
                start_time=start_time,
                end_time=end_time,
                created_by='backfill_script',
                updated_by='backfill_script'
            )
            batch.append(business_hour)

            # Insert batch into the database
            if len(batch) == batch_size:
                db.bulk_save_objects(batch)
                db.commit()
                batch.clear()  # Clear batch after commit

            print(f"Processing business hour {index} of {total_rows} ({index/total_rows:.2%})", end='\r')

    # Insert any remaining records
    if batch:
        db.bulk_save_objects(batch)
        db.commit()

if __name__ == '__main__':
    csv_path = 'app/csv/menu_hours.csv'
    with Session(engine) as db:
        backfill_business_hours(csv_path, db)
    print("Business hours backfill completed successfully.")
