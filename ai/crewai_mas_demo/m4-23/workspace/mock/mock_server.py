from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Mock data for leave records
mock_leave_records = [
    {
        "id": "1",
        "employee_id": "E001",
        "employee_name": "John Doe",
        "leave_type": "vacation",
        "start_date": "2023-10-01",
        "end_date": "2023-10-07",
        "days": 7,
        "apply_time": "2023-09-25T10:00:00Z",
        "status": "approved",
        "approver": "Manager A",
        "reason": "Vacation"
    }
]


class MockServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/v1/leaves':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(mock_leave_records).encode())
        elif self.path.startswith('/api/v1/leaves/'):
            try:
                id = self.path.split('/')[-1]
                leave_record = next(record for record in mock_leave_records if record['id'] == id)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(leave_record).encode())
            except StopIteration:
                self.send_response(404)
                self.end_headers()

    def do_POST(self):
        if self.path == '/api/v1/leaves':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            new_leave_record = json.loads(post_data)
            # Add validation and business logic here
            mock_leave_records.append(new_leave_record)
            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(new_leave_record).encode())

    def do_PUT(self):
        if self.path.startswith('/api/v1/leaves/'):
            content_length = int(self.headers['Content-Length'])
            put_data = self.rfile.read(content_length)
            update_data = json.loads(put_data)
            id = self.path.split('/')[-1]
            # Add validation and business logic here
            for record in mock_leave_records:
                if record['id'] == id:
                    record.update(update_data)
                    break
            else:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(record).encode())

    def do_DELETE(self):
        if self.path.startswith('/api/v1/leaves/'):
            id = self.path.split('/')[-1]
            # Add validation and business logic here
            mock_leave_records[:] = [record for record in mock_leave_records if record['id'] != id]
            self.send_response(204)
            self.end_headers()

    def do_PATCH(self):
        if self.path.startswith('/api/v1/leaves/'):
            content_length = int(self.headers['Content-Length'])
            patch_data = self.rfile.read(content_length)
            update_data = json.loads(patch_data)
            id = self.path.split('/')[-1]
            # Add validation and business logic here
            for record in mock_leave_records:
                if record['id'] == id:
                    record.update(update_data)
                    break
            else:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(record).encode())

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, MockServer)
    print('Starting mock server...')
    httpd.serve_forever()