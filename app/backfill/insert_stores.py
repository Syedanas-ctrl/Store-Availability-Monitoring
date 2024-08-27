import csv
from app.models import Store
from app.database import engine
from sqlalchemy.orm import Session

def backfill_stores(csv_path: str, db: Session):
    with open(csv_path, mode='r') as file:
        total_rows = sum(1 for row in csv.DictReader(file))

    batch_size = 1000
    batch = []

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for index, row in enumerate(reader, start=1):
            store = Store(
                id=int(row['store_id']),
                timezone=row['timezone_str'],
                created_by='backfill_script',
                updated_by='backfill_script'
            )
            batch.append(store)
            
            if len(batch) == batch_size:
                db.bulk_save_objects(batch)
                db.commit()
                batch.clear() 
            
            print(f"Processing store {index} of {total_rows} ({index/total_rows:.2%})", end='\r')

    # Insert any remaining records
    if batch:
        db.bulk_save_objects(batch)
        db.commit()
    
    print(f"\nCompleted processing {total_rows} stores.")

if __name__ == '__main__':
    csv_path = 'app/csv/stores.csv'
    with Session(engine) as db:
        backfill_stores(csv_path, db)
    print("Stores backfill completed successfully.")
