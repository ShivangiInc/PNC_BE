
# FUN ops POC

## Overview

 The project is built using the Django framework and includes features to parse the excel file to save it in a non-relational database. It has functionalities of manipulating the table data and altering the table structure itself. 

## Features

- Feature 1: Handle POST requests to upload an Excel file and replace existing data in MongoDB.
- Feature 2: Handle GET requests to retrieve data from MongoDB and return it as a list of dictionaries.
- Feature 3: Update a specific row based on record_id, or create a new row if record_id is not found.
- Feature 4: Soft-delete a specific row by marking it as deleted.
- Feature 5: Add a new column to every document in the MongoDB collection.
- Feature 6: Soft delete a column from every document in the MongoDB collection.
- Feature 7: Rename a column in every document in the collection.

## Documentation

For detailed API description, please refer to API Documentation.

## Installation

### Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.x installed on your machine
- MongoDB
- pip (Python package installer)
- Virtualenv (optional but recommended)

### Setup Instructions

1. **Create a Virtual Environment**

   python -m venv venv


2. **Activate the Virtual Environment**

   - On Windows:
     venv\Scripts\activate

   - On MacOS/Linux:
     source venv/bin/activate


3. **Install Dependencies**

   pip install -r requirements.txt


4. **Set Up Environment Variables**

   Create a `.env` file in the root directory and add the necessary environment variables.


5. **Run the Development Server**

   python manage.py runserver

   The project will be available at `http://127.0.0.1:8000/`.

