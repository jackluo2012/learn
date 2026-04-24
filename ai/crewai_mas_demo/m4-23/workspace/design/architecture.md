# System Architecture Document

## Overview

The Employee Leave Record Management System is designed to handle CRUD operations on leave records for employees. The system will be built using a simple tech stack with Python FastAPI for the backend and plain HTML + JavaScript for the frontend. Data will be stored in memory using dictionaries.

## Module Division

### Frontend

- **HTML**: For structuring the UI.
- **JavaScript**: For handling form validation, state management, and AJAX requests to the backend.

### Backend

- **FastAPI**: For defining RESTful APIs and handling HTTP requests.
- **In-Memory Storage**: Using Python dictionaries to store leave records.

### Utilities

- **Validation**: For ensuring data integrity and form validation.
- **Date Calculation**: For automatically calculating the number of leave days based on start and end dates.

## Directory Structure

```
workspace/
├── design/
│   ├── architecture.md
│   └── api_spec.md
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── scripts.js
└── backend/
    ├── main.py
    ├── models.py
    └── utils.py
```

## Tech Stack

- **Frontend**: HTML, JavaScript
- **Backend**: Python, FastAPI
- **Data Storage**: In-Memory (Dictionaries)

## Additional Notes

- The frontend will be developed without any frameworks to keep it simple and easy to understand.
- The backend will expose RESTful APIs that can be consumed by the frontend.
- All data will be stored in memory for simplicity and ease of development.