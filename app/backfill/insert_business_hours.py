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

    stores = {store.id: store for store in db.query(Store).all()}
    business_hours = {store_id: {} for store_id in stores}

    current_date = datetime.now().date()
    additional_stores = 0
    missing_business_hours = 0

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for index, row in enumerate(reader, start=1):
            store_id = int(row['store_id'])
            day = int(row['day'])

            if store_id not in stores:
                # Add new store if not found
                store = Store(
                    id=store_id,
                    timezone='America/Chicago',  # default timezone
                    created_by='missing_store_backfill',
                    updated_by='missing_store_backfill'
                )
                db.add(store)
                stores[store_id] = store
                business_hours[store_id] = {}
                additional_stores += 1

            tz = pytz.timezone(stores[store_id].timezone)
            start_time = tz.localize(datetime.combine(current_date, time.fromisoformat(row['start_time_local'] or '00:00:00')))
            end_time = tz.localize(datetime.combine(current_date, time.fromisoformat(row['end_time_local'] or '23:59:59')))

            business_hours[store_id][day] = (start_time, end_time)

            if index % 1000 == 0:
                print(f"Processed {index} of {total_rows} rows ({index/total_rows:.2%})")

    print(f"\nAdditional stores added: {additional_stores}")
    
    batch_size = 1000
    batch = []
    total_business_hours = len(stores) * 7
    processed_business_hours = 0

    for store_id, days in business_hours.items():
        for day in range(7):  # 0 to 6 for all days of the week
            if day not in days:
                missing_business_hours += 1

            start_time, end_time = days.get(day, (
                tz.localize(datetime.combine(current_date, time.min)),
                tz.localize(datetime.combine(current_date, time.max))
            ))

            business_hour = BusinessHour(
                store_id=store_id,
                day_of_week=DayOfWeek(day),
                start_time=start_time,
                end_time=end_time,
                created_by='backfill_script',
                updated_by='backfill_script'
            )
            batch.append(business_hour)
            processed_business_hours += 1

            if len(batch) >= batch_size:
                db.bulk_save_objects(batch)
                db.commit()
                batch.clear()
                print(f"Inserted {processed_business_hours} of {total_business_hours} business hours ({processed_business_hours/total_business_hours:.2%})")

    if batch:
        db.bulk_save_objects(batch)
        db.commit()

    print(f"\nMissing business hours filled: {missing_business_hours}")
    print(f"Total business hours inserted: {total_business_hours}")

if __name__ == '__main__':
    csv_path = 'app/csv/menu_hours.csv'
    with Session(engine) as db:
        backfill_business_hours(csv_path, db)
    print("Business hours backfill completed successfully.")
