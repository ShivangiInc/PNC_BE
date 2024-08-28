from django.db import models
import pymongo

url = "mongodb://localhost:27017"
client = pymongo.MongoClient(url)

db = client["table_records"]
table_data = db["records"]
deleted_columns = db["deleted_columns"]
