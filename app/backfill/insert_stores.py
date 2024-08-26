import csv
from app.models import Store
from app.database import engine
from sqlalchemy.orm import Session

def backfill_stores(csv_path: str, db: Session):
    with open(csv_path, mode='r') as file:
        total_rows = sum(1 for row in csv.DictReader(file))

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for index, row in enumerate(reader, start=1):
            store = Store(
                id=int(row['store_id']),
                timezone=row['timezone_str'],
                created_by='backfill_script',
                updated_by='backfill_script'
            )
            db.add(store)
            
            # Commit every 1000 rows to avoid long-running transactions
            if index % 1000 == 0:
                db.commit()
            
            print(f"Processing store {index} of {total_rows} ({index/total_rows:.2%})", end='\r')

    db.commit()
    print(f"\nCompleted processing {total_rows} stores.")

if __name__ == '__main__':
    csv_path = 'app/csv/stores.csv'
    with Session(engine) as db:
        backfill_stores(csv_path, db)
    print("Stores backfill completed successfully.")