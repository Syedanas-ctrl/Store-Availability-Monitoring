# Welcome to Loop - Store Monitoring

This is build on -
FastAPI
Celery
Redis
PostgreSQL

SQLAlchemy
alembic

----------------------------------------------------------------------------------------------------
### High-level architecture:
[Client] <-> [FastAPI Web Server] <-> [PostgreSQL Database]
                    ^
                    |
                    v   
[Celery Worker] <-> [Redis (Message Broker)]

----------------------------------------------------------------------------------------------------

### Repository structure

**alembic**
This is where all the migrations are stored.

**app/backfill**
All the backfill scripts are stored here.

**app/report**
models, services etc. related to the report are stored here.

**app/store**
models, services etc. related to the store are stored here.

**app/business_hours**
models, services etc. related to the business hours are stored here.

**app/store_status**
models, services etc. related to the store status are stored here.

**app/base.py**
This is the base model for all the models. contains all the common fields for all the models.
Like id, created_at, updated_at, deleted_at etc.

**app/crud.py**
This is the CRUD operations for the models.

**app/database.py**
This is the database connection for the app.

**app/tasks.py**
celery tasks and configurations are defined here.

**app/main.py**
This is the entry point for the app.

----------------------------------------------------------------------------------------------------
## How to run the project

### Prerequisites
- Docker

### Run the project

1. Clone the repository
2. Run the command `docker-compose up --build`
3. Generate migrations `alembic revision --autogenerate -m "migration_name"`
4. Apply migrations `alembic upgrade head`
**Note - you need to have csv files in app/csv folder (please rename to menu_hours.csv, stores.csv, store_status.csv)**
5. Backfill stores `python -m app.backfill.stores`
6. Backfill business hours `python -m app.backfill.business_hours`
7. Backfill store status `python -m app.backfill.store_status`
8. Port 8000 should be exposed for the fastapi server. API is ready to use.

----------------------------------------------------------------------------------------------------

### API Details

#### Trigger Report

**Endpoint** - POST /trigger_report
**Description** - This endpoint is used to trigger the report generation.
**Input** - None
**Output** - report_id

**Sample Request**
```
curl -X POST http://localhost:8000/trigger_report
```

#### Get Report

**Endpoint** - GET /get_report/{report_id}
**Description** - This endpoint is used to get the report.
**Input** - report_id
**Output** - Status of the report. and report in csv format

**Sample Request**
```
curl http://localhost:8000/get_report/report_id
```
