from pymongo import MongoClient
from backend.app.core.config import settings
from upstash_redis import Redis

# MongoDB Database
mongodb_client = MongoClient(settings.MONGODB_URL)
mongodb_db = mongodb_client["lms_support"]

# Redis Client
redis_client = Redis(url=settings.REDIS_URL, token=settings.REDIS_TOKEN)

def get_mongodb():
    return mongodb_db

def get_redis():
    return redis_client