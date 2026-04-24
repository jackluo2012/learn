# API Specification for Employee Leave Record Management

## Overview
This document defines the RESTful API endpoints for managing employee leave records. The API will be used to perform CRUD operations on leave records.

## Base URL
The base URL for all API endpoints is `http://localhost:8000/api/v1`.

## Endpoints

### 1. List All Leave Records
- **Path**: `/leaves`
- **Method**: `GET`
- **Request Body**: None
- **Response Body**:
    ```json
    [
        {
            "id": "string",
            "employee_id": "string",
            "employee_name": "string",
            "leave_type": "enum",
            "start_date": "date",
            "end_date": "date",
            "days": "number",
            "apply_time": "datetime",
            "status": "enum",
            "approver": "string",
            "reason": "string"
        }
    ]
    ```
- **Error Codes**: 
    - `400 Bad Request`: If the request is malformed.
    - `404 Not Found`: If no leave records are found.

### 2. Get a Specific Leave Record
- **Path**: `/leaves/{id}`
- **Method**: `GET`
- **Request Body**: None
- **Response Body**:
    ```json
    {
        "id": "string",
        "employee_id": "string",
        "employee_name": "string",
        "leave_type": "enum",
        "start_date": "date",
        "end_date": "date",
        "days": "number",
        "apply_time": "datetime",
        "status": "enum",
        "approver": "string",
        "reason": "string"
    }
    ```
- **Error Codes**: 
    - `400 Bad Request`: If the request is malformed.
    - `404 Not Found`: If the leave record with the specified ID is not found.

### 3. Create a New Leave Record
- **Path**: `/leaves`
- **Method**: `POST`
- **Request Body**:
    ```json
    {
        "employee_id": "string",
        "employee_name": "string",
        "leave_type": "enum",
        "start_date": "date",
        "end_date": "date",
        "reason": "string"
    }
    ```
- **Response Body**:
    ```json
    {
        "id": "string",
        "employee_id": "string",
        "employee_name": "string",
        "leave_type": "enum",
        "start_date": "date",
        "end_date": "date",
        "days": "number",
        "apply_time": "datetime",
        "status": "enum",
        "approver": "string",
        "reason": "string"
    }
    ```
- **Error Codes**: 
    - `400 Bad Request`: If the request is malformed or if the start_date is greater than the end_date.
    - `409 Conflict`: If the leave record already exists.

### 4. Update a Leave Record
- **Path**: `/leaves/{id}`
- **Method**: `PUT`
- **Request Body**:
    ```json
    {
        "employee_id": "string",
        "employee_name": "string",
        "leave_type": "enum",
        "start_date": "date",
        "end_date": "date",
        "reason": "string"
    }
    ```
- **Response Body**:
    ```json
    {
        "id": "string",
        "employee_id": "string",
        "employee_name": "string",
        "leave_type": "enum",
        "start_date": "date",
        "end_date": "date",
        "days": "number",
        "apply_time": "datetime",
        "status": "enum",
        "approver": "string",
        "reason": "string"
    }
    ```
- **Error Codes**: 
    - `400 Bad Request`: If the request is malformed or if the start_date is greater than the end_date.
    - `404 Not Found`: If the leave record with the specified ID is not found.
    - `409 Conflict`: If the leave record already exists.

### 5. Delete a Leave Record
- **Path**: `/leaves/{id}`
- **Method**: `DELETE`
- **Request Body**: None
- **Response Body**: None
- **Error Codes**: 
    - `400 Bad Request`: If the request is malformed.
    - `404 Not Found`: If the leave record with the specified ID is not found.

### 6. Approve/Reject a Leave Record
- **Path**: `/leaves/{id}/approve`
- **Method**: `PUT`
- **Request Body**:
    ```json
    {
        "status": "enum"
    }
    ```
- **Response Body**:
    ```json
    {
        "id": "string",
        "employee_id": "string",
        ``