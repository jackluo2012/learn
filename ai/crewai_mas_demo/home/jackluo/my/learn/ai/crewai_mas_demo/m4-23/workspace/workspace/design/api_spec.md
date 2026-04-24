The file `/home/jackluo/my/learn/ai/crewai_mas_demo/m4-23/workspace/design/api_spec.md` has been written with the API specifications as per the provided requirements. Below is the full content of the file:

```markdown
# API Specification Document

## List All Leaves

- **Path**: `/leaves`
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
- **Error Codes**: 400 Bad Request, 500 Internal Server Error

## Create New Leave Record

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
  "message": "Leave record created successfully"
}
```
- **Error Codes**: 400 Bad Request, 409 Conflict, 500 Internal Server Error

## Update Leave Record

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
  "message": "Leave record updated successfully"
}
```
- **Error Codes**: 400 Bad Request, 404 Not Found, 409 Conflict, 500 Internal Server Error

## Delete Leave Record

- **Path**: `/leaves/{id}`
- **Method**: `DELETE`
- **Request Body**: None
- **Response Body**:
```json
{
  "message": "Leave record deleted successfully"
}
```
- **Error Codes**: 400 Bad Request, 404 Not Found, 409 Conflict, 500 Internal Server Error

## Approve/Deny Leave Record

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
  "message": "Leave record approved/denied successfully"
}
```
- **Error Codes**: 400 Bad Request, 404 Not Found, 409 Conflict, 500 Internal Server Error
```

Final Answer: `/home/jackluo/my/learn/ai/crewai_mas_demo/m4-23/workspace/design/api_spec.md`