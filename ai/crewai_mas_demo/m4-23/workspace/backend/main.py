from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uuid

app = FastAPI()

# In-memory database simulation
database = {}

# Pydantic model for leave record
class LeaveRecord(BaseModel):
    id: str
    employee_id: str
    start_date: str
    end_date: str
    reason: str
    status: str


@app.post('/leaves/', response_model=LeaveRecord)
def create_leave_record(leave_record: LeaveRecord):
    leave_record.id = str(uuid.uuid4())
    database[leave_record.id] = leave_record
    return leave_record


@app.get('/leaves/', response_model=List[LeaveRecord])
def get_all_leaves():
    return list(database.values())


@app.put('/leaves/{id}', response_model=LeaveRecord)
def update_leave_record(id: str, updated_leave_record: LeaveRecord):
    if id in database:
        database[id] = updated_leave_record
        return database[id]
    else:
        raise HTTPException(status_code=404, detail='Leave record not found')


@app.delete('/leaves/{id}')
def delete_leave_record(id: str):
    if id in database:
        del database[id]
        return '', 204
    else:
        raise HTTPException(status_code=404, detail='Leave record not found')


@app.patch('/leaves/{id}/status')
def change_status(id: str, new_status: str):
    if id in database:
        database[id].status = new_status
        return database[id]
    else:
        raise HTTPException(status_code=404, detail='Leave record not found')