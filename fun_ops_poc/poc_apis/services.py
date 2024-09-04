import pandas as pd
from bson import ObjectId
import math
from .models import table_data, deleted_columns


# def process_excel_file(file):
#     """
#     Process the uploaded Excel file and return the data as a list of dictionaries.
#     """
#     try:
#         df = pd.read_excel(file)
#         df.columns = df.columns.map(str)
#         records = df.to_dict(orient="records")
#         return records
#     except Exception as e:
#         raise ValueError(f"Error reading Excel file: {str(e)}")

def process_csv_file(file):
    # Read the CSV file into a DataFrame using pandas
    df = pd.read_csv(file)
    # Convert DataFrame to a list of dictionaries for MongoDB insertion
    records = df.to_dict(orient="records")
    return records


def process_excel_file(file):
    # Read the Excel file into a DataFrame using pandas
    df = pd.read_excel(file)
    # Convert DataFrame to a list of dictionaries for MongoDB insertion
    records = df.to_dict(orient="records")
    return records


def process_tsv_file(file):
    # Read the TSV file into a DataFrame using pandas
    df = pd.read_csv(file, delimiter="\t")
    # Convert DataFrame to a list of dictionaries for MongoDB insertion
    records = df.to_dict(orient="records")
    return records


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
        deleted_columns.delete_many(
            {}
        )  # Delete all documents in the deleted_columns collection
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


def fetch_all_deleted_column_names():
    """
    Fetch all column names from documents where 'is_deleted' is True.
    """
    try:
        # Fetch all records where is_deleted is True
        deleted_columns_list = deleted_columns.find(
            {"is_deleted": True}, {"_id": 0, "column_name": 1}
        )

        # Extract the column_name from each document
        column_names = [doc["column_name"] for doc in deleted_columns_list]
        print(column_names)
        return column_names

    except Exception as e:
        print(f"Error fetching deleted columns from MongoDB: {str(e)}")
        return []

def fetch_all_deleted_by_admin_column_names():
    """
    Fetch all column names from documents where 'deleted_by_admin' is True.
    """
    try:
        # Fetch all records where deleted_by_admin is True
        deleted_by_admin_columns_list = deleted_columns.find(
            {"deleted_by_admin": True}, {"_id": 0, "column_name": 1}
        )

        # Extract the column_name from each document
        column_names = [doc["column_name"] for doc in deleted_by_admin_columns_list]
        print(column_names)
        return column_names

    except Exception as e:
        print(f"Error fetching deleted columns from MongoDB: {str(e)}")
        return []
    
def fetch_all_rejected_by_admin_column_names():
    try:
        # Fetch all records where deleted_by_admin is True
        rejected_by_admin_columns_list = deleted_columns.find(
            {"deleted_by_admin": False}, {"_id": 0, "column_name": 1}
        )
        column_names = [doc["column_name"] for doc in rejected_by_admin_columns_list]
        print(column_names)
        return column_names

    except Exception as e:
        print(f"Error fetching deleted columns from MongoDB: {str(e)}")
        return []
    
def sanitize_data(data):
    if isinstance(data, list):
        return [sanitize_data(item) for item in data]
    elif isinstance(data, dict):
        return {key: sanitize_data(value) for key, value in data.items()}
    elif isinstance(data, float) and (math.isnan(data) or math.isinf(data)):
        return None
    return data

def fetch_all_deleted_by_admin_record_names():
    try:
        # Fetch all records where deleted_by_admin is True
        deleted_by_admin_record_list = list(
            table_data.find({"deleted_by_admin": True}, {"_id": 0})
        )
        
        # Sanitize the data to handle any NaN or invalid values
        sanitized_data = sanitize_data(deleted_by_admin_record_list)
        return sanitized_data

    except Exception as e:
        print(f"Error fetching deleted records from MongoDB: {str(e)}")
        return []
    
def fetch_all_rejected_by_admin_record_names():
    try:
        # Fetch all records where deleted_by_admin is False
        rejected_by_admin_record_list = list(
            table_data.find({"deleted_by_admin": False}, {"_id": 0})
        )
        
        # Sanitize the data to handle any NaN or invalid values
        sanitized_data = sanitize_data(rejected_by_admin_record_list)
        return sanitized_data

    except Exception as e:
        print(f"Error fetching rejected records from MongoDB: {str(e)}")
        return []
    
def fetch_all_records():
    # Fetch all records from MongoDB
    records = list(table_data.find({}))
    # Process records to replace NaN values
    for record in records:
        # Convert MongoDB ObjectId to string
        record["_id"] = str(record["_id"])  # Convert ObjectId to string
        # Replace NaN values with None
        for key, value in record.items():
            if isinstance(value, float) and (
                pd.isna(value) or value == float("inf") or value == float("-inf")
            ):
                record[key] = None
    return records

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
