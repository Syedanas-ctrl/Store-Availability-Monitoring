import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    ENVIRONMENT=os.getenv('ENVIRONMENT')
    ORIGIN=os.getenv('ORIGIN')
    #redis
    REDIS_HOST=os.getenv('REDIS_HOST')
    REDIS_PORT=os.getenv('REDIS_PORT')
    REDIS_DB=os.getenv('REDIS_DB')
