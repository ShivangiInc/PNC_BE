# API Documentation

## 1. Excel Upload

**Endpoint:** `POST /api/upload/`

**Description:**  
Handle POST requests to upload an Excel file and replace existing data in MongoDB.

**Request:**

- **Content-Type:** `multipart/form-data`
- **File:** `file` (required) - The Excel file to upload.

**Responses:**

- **201 Created:**
  ```json
  {
    "message": "Data successfully replaced in MongoDB"
  }
  ```
- **400 Bad Request:**
  ```json
  {
    "error": "No file uploaded"
  }
  ```
  OR
  ```json
  {
    "error": "Error processing file: <error_message>"
  }
  ```

**Example Request:**
```http
POST /api/upload/
Content-Type: multipart/form-data

file: <path_to_excel_file>
```

## 2. Fetch Excel Data

**Endpoint:** `GET /api/data/`

**Description:**  
The ExcelDataView API retrieves data from MongoDB and returns it as a list of records. It also includes a list of columns that have been marked as "soft deleted."

**Request:**

- **No parameters required.**

**Responses:**

Status Code: 200 OK
Content Type: application/json
Response Body: A JSON object containing two keys:
records: A list of dictionaries representing the records from the MongoDB collection.
deleted_columns: A list of strings representing the names of columns that have been soft deleted.

**Example Request:**
```http
GET /api/data/
```

## 3. Modify or Create Record

**Endpoint:** `POST /api/create_or_update_record/`  
**Endpoint for specific record:** `POST /api/create_or_update_record/{record_id}/`

**Description:**  
Update a specific row based on `record_id`, or create a new row if `record_id` is not found.

**Request:**

- **Body:** 
  ```json
  {
    "field1": "value1",
    "field2": "value2"
  }
  ```

**Responses:**

- **201 Created:**
  ```json
  {
    "message": "New row created successfully",
    "id": "new_record_id"
  }
  ```
- **200 OK:**
  ```json
  {
    "message": "Record updated successfully"
  }
  ```
- **400 Bad Request:**
  ```json
  {
    "error": "No valid fields to update"
  }
  ```
- **404 Not Found:**
  ```json
  {
    "error": "Record not found"
  }
  ```
- **500 Internal Server Error:**
  ```json
  {
    "error": "Error processing request in MongoDB: <error_message>"
  }
  ```

**Example Request to Create:**
```http
POST /api/create_or_update_record/
Content-Type: application/json

{
  "field1": "value1",
  "field2": "value2"
}
```

**Example Request to Update:**
```http
POST /api/create_or_update_record/66b9fb790b2700bfd39597b8/
Content-Type: application/json

{
  "field1": "updated_value"
}
```

## 4. Soft Delete Record

**Endpoint:** `DELETE /api/create_or_update_record/{record_id}/`

**Description:**  
Soft-delete a specific row by marking it as deleted.

**Request:**

- **No body required.**

**Responses:**

- **200 OK:**
  ```json
  {
    "message": "Record marked as deleted successfully"
  }
  ```
- **404 Not Found:**
  ```json
  {
    "error": "Record not found"
  }
  ```
- **500 Internal Server Error:**
  ```json
  {
    "error": "Error marking record as deleted in MongoDB: <error_message>"
  }
  ```

**Example Request:**
```http
DELETE /api/create_or_update_record/66b9fb790b2700bfd39597ba/
```

## 5. Add Column

**Endpoint:** `POST /api/add-column/`

**Description:**  
Add a new column to every document in the MongoDB collection.

**Request:**

- **Body:**
  ```json
  {
    "column_name": "new_column_name"
  }
  ```

**Responses:**

- **200 OK:**
  ```json
  {
    "message": "Column 'new_column_name' added to X documents"
  }
  ```
- **400 Bad Request:**
  ```json
  {
    "error": "Column name is required"
  }
  ```
- **500 Internal Server Error:**
  ```json
  {
    "error": "Error adding column to MongoDB: <error_message>"
  }
  ```

**Example Request:**
```http
POST /api/add-column/
Content-Type: application/json

{
  "column_name": "new_column"
}
```
### SoftDeleteColumnView API Documentation

#### **Endpoint: Soft Delete Column**

- **URL:** `http://localhost:8000/api/soft-delete-column/`
- **Method:** `POST`
- **Description:** Marks a specific column as "soft-deleted" by adding an entry to a separate tracking collection. The original column in the main collection remains intact and unaffected.

#### **Request Parameters:**

- **Headers:**
  - `Content-Type: application/json`

- **Body Parameters:**
  - `column_name` (string, required): The name of the column to be soft-deleted.

#### **Example Request:**

```json
{
    "column_name": "example_column_name"
}
```

#### **Response:**

- **Success Response:**
  - **Status Code:** `200 OK`
  - **Response Body:**

    ```json
    {
        "message": "Column 'example_column_name' has been marked as deleted in the tracking collection."
    }
    ```

- **Error Responses:**

  - **Status Code:** `400 Bad Request`
    - **Response Body:** If the `column_name` is not provided.
    
    ```json
    {
        "error": "Column name is required"
    }
    ```

  - **Status Code:** `500 Internal Server Error`
    - **Response Body:** If there is an error processing the request.

    ```json
    {
        "error": "Error marking column as deleted in MongoDB: <error_message>"
    }
    ```

## 6. Soft Delete Column

**Endpoint:** `POST /api/soft-delete-column/`

**Description:**  
The API first checks if the `column_name` is provided in the request body. If not, it returns a `400 Bad Request` error.
- The API checks if the column already exists in the `deleted_columns` collection:
     - If it exists, it updates the `is_deleted` field to `True`.
     - If it doesn't exist, it creates a new document in the `deleted_columns` collection with `column_name` and sets `is_deleted` to `True`.


**Request:**

- **Body:**
  ```json
  {
    "column_name": "column_to_remove"
  }
  ```

**Responses:**
   - A success message is returned if the operation is successful.
   - Any exceptions during the process result in a `500 Internal Server Error` with details about the error.

**Example Request:**
```http
POST /api/soft-delete-column/
Content-Type: application/json

{
  "column_name": "obsolete_column"
}
```

## 7. Rename Column

**Endpoint:** `POST /api/rename-column/`

**Description:**  
Rename a column in every document in the collection.

**Request:**

- **Body:**
  ```json
  {
    "old_column_name": "old_name",
    "new_column_name": "new_name"
  }
  ```

**Responses:**

- **200 OK:**
  ```json
  {
    "message": "Column 'old_name' renamed to 'new_name' in X documents"
  }
  ```
- **400 Bad Request:**
  ```json
  {
    "error": "Both 'old_column_name' and 'new_column_name' are required"
  }
  ```
- **500 Internal Server Error:**
  ```json
  {
    "error": "Error renaming column in MongoDB: <error_message>"
  }
  ```

**Example Request:**
```http
POST /api/rename-column/
Content-Type: application/json

{
  "old_column_name": "old_col",
  "new_column_name": "new_col"
}
```

## 8. Export as pdf
## 9. Export as excel
## 10. Soft deleting by admin


