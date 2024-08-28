import pandas as pd
from bson import ObjectId
from .models import table_data, deleted_columns


def process_excel_file(file):
    """
    Process the uploaded Excel file and return the data as a list of dictionaries.
    """
    try:
        df = pd.read_excel(file)
        df.columns = df.columns.map(str)
        records = df.to_dict(orient="records")
        return records
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {str(e)}")


def clear_existing_records():
    """
    Clear existing records from the MongoDB collection.
    """
    try:
        table_data.delete_many({})  # Remove all documents from the collection
    except Exception as e:
        raise ValueError(f"Error clearing existing data in MongoDB: {str(e)}")

def clear_deleted_columns():
    """
    Clear all records from the deleted_columns collection.
    """
    try:
        deleted_columns.delete_many({})  # Delete all documents in the deleted_columns collection
    except Exception as e:
        print(f"Error clearing deleted columns from MongoDB: {str(e)}")

def insert_records(records):
    """
    Insert records into MongoDB.
    """
    try:
        table_data.insert_many(records)
    except Exception as e:
        raise ValueError(f"Error inserting data into MongoDB: {str(e)}")


def fetch_all_records():
    """
    Fetch all records from MongoDB and return them as a list of dictionaries.
    """
    try:
        records = list(table_data.find({}, {"_id": 0}))
        return pd.DataFrame(records).fillna("").to_dict(orient="records")
    except Exception as e:
        raise ValueError(f"Error fetching data from MongoDB: {str(e)}")


def update_record(record_id, update_data):
    """
    Update a specific row based on record_id. If the record does not exist, return an error.
    """
    try:
        object_id = ObjectId(record_id)
        current_document = table_data.find_one({"_id": object_id})
        if not current_document:
            raise ValueError("Record not found")

        allowed_fields = set(current_document.keys())
        filtered_update_data = {
            key: value for key, value in update_data.items() if key in allowed_fields
        }

        if not filtered_update_data:
            raise ValueError("No valid fields to update")

        result = table_data.update_one(
            {"_id": object_id}, {"$set": filtered_update_data}
        )
        if result.matched_count == 0:
            raise ValueError("Record not found")

        return {"message": "Record updated successfully"}
    except Exception as e:
        raise ValueError(f"Error updating record in MongoDB: {str(e)}")


def create_record(new_data):
    """
    Create a new row in the MongoDB collection.
    """
    try:
        result = table_data.insert_one(new_data)
        print("entered")
        return {
            "message": "New row created successfully",
            "id": str(result.inserted_id),
        }
    except Exception as e:
        raise ValueError(f"Error creating new row in MongoDB: {str(e)}")


def soft_delete_record(record_id):
    """
    Soft-delete a specific row by marking it as deleted.
    """
    try:
        result = table_data.update_one(
            {"_id": ObjectId(record_id)}, {"$set": {"marked_as_deleted": True}}
        )
        if result.matched_count == 0:
            raise ValueError("Record not found")

        return {"message": "Record marked as deleted successfully"}
    except Exception as e:
        raise ValueError(f"Error marking record as deleted in MongoDB: {str(e)}")
