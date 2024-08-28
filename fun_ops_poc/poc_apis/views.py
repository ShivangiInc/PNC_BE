import pandas as pd
from io import BytesIO
from django.http import HttpResponse
import logging
from bson import ObjectId
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views import View
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from .models import table_data, deleted_columns
from .services import (
    process_excel_file,
    insert_records,
    clear_existing_records,
    clear_deleted_columns
)

logging.basicConfig(level=logging.DEBUG)

def fetch_all_deleted_column_names():
    """
    Fetch all column names from documents where 'is_deleted' is True.
    """
    try:
        # Fetch all records where is_deleted is True
        deleted_columns_list = deleted_columns.find({"is_deleted": True}, {"_id": 0, "column_name": 1})

        # Extract the column_name from each document
        column_names = [doc["column_name"] for doc in deleted_columns_list]
        print(column_names)
        return column_names

    except Exception as e:
        print(f"Error fetching deleted columns from MongoDB: {str(e)}")
        return []

def fetch_all_records():
    # Fetch all records from MongoDB
    records = list(table_data.find({}))
    # Process records to replace NaN values
    for record in records:
        # Convert MongoDB ObjectId to string
        record['_id'] = str(record['_id'])  # Convert ObjectId to string
        # Replace NaN values with None
        for key, value in record.items():
            if isinstance(value, float) and (pd.isna(value) or value == float('inf') or value == float('-inf')):
                record[key] = None
    return records

def process_csv_file(file):
    # Read the CSV file into a DataFrame using pandas
    df = pd.read_csv(file)
    # Convert DataFrame to a list of dictionaries for MongoDB insertion
    records = df.to_dict(orient='records')
    return records

def process_excel_file(file):
    # Read the Excel file into a DataFrame using pandas
    df = pd.read_excel(file)
    # Convert DataFrame to a list of dictionaries for MongoDB insertion
    records = df.to_dict(orient='records')
    return records

class ExcelUploadView(APIView):
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to upload an Excel or CSV file and replace existing data in MongoDB.
        http://localhost:8000/api/upload/
        """
        if "file" not in request.FILES:
            return Response(
                {"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES["file"]
        file_name = uploaded_file.name

        try:
            if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
                # Process Excel file
                records = process_excel_file(uploaded_file)
            elif file_name.endswith(".csv"):
                # Process CSV file
                records = process_csv_file(uploaded_file)
            else:
                return Response(
                    {"error": "Unsupported file format. Please upload an Excel or CSV file."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Clear existing data and insert new records
            clear_deleted_columns()
            clear_existing_records()
            insert_records(records)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "Data successfully replaced in MongoDB"},
            status=status.HTTP_201_CREATED,
        )


class ExcelDataView(APIView):
    """
    Handle GET requests to retrieve data from MongoDB and return it as a list of dictionaries.
    http://localhost:8000/api/data/
    """

    def get(self, request, *args, **kwargs):
        try:
            # Fetch all records
            records = fetch_all_records()
            
            # Fetch deleted columns
            deleted_columns = fetch_all_deleted_column_names()

            # Combine the data into a single response
            response_data = {
                "records": records,
                "deleted_columns": deleted_columns,
            }

        except ValueError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(response_data, status=status.HTTP_200_OK)


class ModifyRecordView(APIView):
    def post(self, request, record_id=None, *args, **kwargs):
        """
        Update a specific row based on record_id, or create a new row if record_id is not found.
        Create new record: http://localhost:8000/api/create_or_update_record/
        Update record: http://localhost:8000/api/create_or_update_record/66b9fb790b2700bfd39597b8/
        """
        try:
            update_data = request.data

            if record_id:
                # Update an existing record
                object_id = ObjectId(record_id)
                current_document = table_data.find_one({"_id": object_id})

                if not current_document:
                    return Response(
                        {"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND
                    )

                # Filter out any fields not in the current document
                allowed_fields = set(current_document.keys())
                filtered_update_data = {
                    key: value
                    for key, value in update_data.items()
                    if key in allowed_fields
                }

                if not filtered_update_data:
                    return Response(
                        {"error": "No valid fields to update"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                result = table_data.update_one(
                    {"_id": object_id}, {"$set": filtered_update_data}
                )

                if result.matched_count == 0:
                    return Response(
                        {"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND
                    )

                return Response(
                    {"message": "Record updated successfully"},
                    status=status.HTTP_200_OK,
                )
            else:
                # Create a new record
                result = table_data.insert_one(update_data)
                return Response(
                    {
                        "message": "New row created successfully",
                        "id": str(result.inserted_id),
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            return Response(
                {"error": f"Error processing request in MongoDB: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, record_id, *args, **kwargs):
        """
        Soft-delete a specific row by marking it as deleted.
        http://localhost:8000/api/create_or_update_record/66b9fb790b2700bfd39597ba/
        """
        try:
            result = table_data.update_one(
                {"_id": ObjectId(record_id)}, {"$set": {"is_deleted": True}}
            )

            if result.matched_count == 0:
                return Response(
                    {"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {"message": "Record marked as deleted successfully"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Error marking record as deleted in MongoDB: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AddColumnView(APIView):
    def post(self, request, *args, **kwargs):
        """
        Add a new column to every document in the MongoDB collection.
        http://localhost:8000/api/add-column/
        """
        try:
            column_name = request.data.get("column_name")
            if not column_name:
                return Response(
                    {"error": "Column name is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            result = table_data.update_many({}, {"$set": {column_name: None}})

            return Response(
                {
                    "message": f"Column '{column_name}' added to {result.modified_count} documents"
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Error adding column to MongoDB: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SoftDeleteColumnView(APIView):
    def post(self, request, *args, **kwargs):
        """
        Mark a column as soft-deleted by adding an entry to a separate collection.
        The original column in the main collection will remain unaffected.
        Endpoint: http://localhost:8000/api/soft-delete-column/
        """
        try:
            column_name = request.data.get("column_name")
            if not column_name:
                return Response(
                    {"error": "Column name is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if the column is already in the `deleted_columns` collection
            existing_entry = deleted_columns.find_one({"column_name": column_name})

            if existing_entry:
                # If it exists, update the "is_deleted" field to True
                deleted_columns.update_one(
                    {"column_name": column_name}, {"$set": {"is_deleted": True}}
                )
            else:
                # If it does not exist, create a new document for the column
                deleted_columns.insert_one(
                    {"column_name": column_name, "is_deleted": True}
                )

            return Response(
                {
                    "message": f"Column '{column_name}' has been marked as deleted in the tracking collection."
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Error marking column as deleted in MongoDB: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RenameColumnView(APIView):
    def post(self, request, *args, **kwargs):
        """
        Rename a column in every document in the collection.
        Takes 'old_column_name' and 'new_column_name' as input.
        http://localhost:8000/api/rename-column/
        """
        try:
            old_column_name = request.data.get("old_column_name")
            new_column_name = request.data.get("new_column_name")

            if not old_column_name or not new_column_name:
                return Response(
                    {
                        "error": "Both 'old_column_name' and 'new_column_name' are required"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            result = table_data.update_many(
                {},
                [
                    {"$set": {new_column_name: "$" + old_column_name}},
                    {"$unset": old_column_name},
                ],
            )

            return Response(
                {
                    "message": f"Column '{old_column_name}' renamed to '{new_column_name}' in {result.modified_count} documents"
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Error renaming column in MongoDB: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class ExcelExportView(View):
    def get(self, request, *args, **kwargs):
        # Fetch data from the MongoDB collection
        mongo_data = list(table_data.find({}, {'_id': 0}))  # Query without '_id' field

        # Convert the data to a DataFrame
        df = pd.DataFrame(mongo_data)

        # Save the DataFrame to a BytesIO object
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        buffer.seek(0)

        # Create the HTTP response with the appropriate content type and headers
        response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="data.xlsx"'

        return response
    
class PdfExportView(View):
    def get(self, request, *args, **kwargs):
        # Fetch records from MongoDB
        records = fetch_all_records()

        # Convert records to DataFrame
        df = pd.DataFrame(records)

        # Drop the '_id' column if it exists
        if '_id' in df.columns:
            df = df.drop(columns=['_id'])

        # Convert DataFrame to a list of lists (rows)
        table_data = [df.columns.tolist()] + df.values.tolist()

        # Estimate the width of each column
        col_widths = [max([len(str(item)) for item in col]) * 0.1 * inch for col in zip(*table_data)]

        # Calculate the total width of the table
        total_width = sum(col_widths)

        # Set page size dynamically based on the table width
        page_width = total_width + 2 * inch  # Add some padding
        page_size = (page_width, 11 * inch)  # Keep height standard (11 inches for A4 height)

        # Create a BytesIO buffer for the PDF
        pdf_buffer = BytesIO()

        # Create the PDF document and canvas
        doc = SimpleDocTemplate(pdf_buffer, pagesize=page_size)
        elements = []

        # Create a Table object from the data with calculated column widths
        table = Table(table_data, colWidths=col_widths)

        # Apply some table styling
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        table.setStyle(style)

        # Add the table to the document elements
        elements.append(table)

        # Build the PDF document
        doc.build(elements)

        # Get PDF data from the buffer
        pdf = pdf_buffer.getvalue()
        pdf_buffer.close()

        # Create an HTTP response with the PDF content
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="table_data.pdf"'

        return response
    
class DeletionApprovedView(APIView):
    def delete(self, request, record_id, *args, **kwargs):
        """
        Soft deleting the fields approved by admin.
        http://localhost:8000/api/deleted_by_admin/66b9fb790b2700bfd39597ba/
        """
        try:
            result = deleted_columns.update_one(
                {"_id": ObjectId(record_id)}, {"$set": {"deleted_by_admin": True}}
            )

            if result.matched_count == 0:
                return Response(
                    {"error": "Record not found"}, status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {"message": "Record marked as deleted successfully"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Error marking record as deleted in MongoDB: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
   