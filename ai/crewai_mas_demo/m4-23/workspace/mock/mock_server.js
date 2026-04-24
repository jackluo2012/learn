// Mock server for Employee Leave Management System
const express = require('express');
const app = express();
const PORT = 3000;

// Mock data
let leaves = [
    {
        id: '1',
        employeeId: 'E001',
        startDate: '2023-09-01',
        endDate: '2023-09-05',
        status: 'approved'
    },
    {
        id: '2',
        employeeId: 'E002',
        startDate: '2023-08-15',
        endDate: '2023-08-20',
        status: 'pending'
    }
];

app.get('/leaves', (req, res) => {
    res.json(leaves);
});

app.post('/leaves', (req, res) => {
    const newLeave = req.body;
    newLeave.id = (leaves.length + 1).toString();
    leaves.push(newLeave);
    res.status(201).json(newLeave);
});

app.put('/leaves/:leave_id', (req, res) => {
    const { leave_id } = req.params;
    const updatedLeave = req.body;
    const index = leaves.findIndex(leave => leave.id === leave_id);
    if (index !== -1) {
        leaves[index] = updatedLeave;
        res.json(leaves[index]);
    } else {
        res.status(404).send('Leave not found');
    }
});

app.delete('/leaves/:leave_id', (req, res) => {
    const { leave_id } = req.params;
    const index = leaves.findIndex(leave => leave.id === leave_id);
    if (index !== -1) {
        leaves.splice(index, 1);
        res.send();
    } else {
        res.status(404).send('Leave not found');
    }
});

app.get('/leaves/:employee_id', (req, res) => {
    const { employee_id } = req.params;
    const employeeLeaves = leaves.filter(leave => leave.employeeId === employee_id);
    res.json(employeeLeaves);
});

app.get('/leaves/status/:status', (req, res) => {
    const { status } = req.params;
    const statusLeaves = leaves.filter(leave => leave.status === status);
    res.json(statusLeaves);
});

app.listen(PORT, () => {
    console.log(`Mock server running on port ${PORT}`);
});