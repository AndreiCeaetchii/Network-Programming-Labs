import socket
import os
import sys
import threading
import time
from urllib.parse import unquote
from datetime import datetime, timedelta
from collections import defaultdict, deque


class HTTPServer:
    def __init__(self, host='localhost', port=8080, directory='./public', max_threads=10):
        self.host = host
        self.port = port
        self.directory = os.path.abspath(directory)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.max_threads = max_threads
        self.thread_pool = []
        self.active_threads = 0
        self.thread_lock = threading.Lock()

        self.file_counters = defaultdict(int)
        self.counter_lock = threading.Lock()

        self.rate_limit = 5
        self.rate_limit_window = 1.0
        self.client_requests = defaultdict(lambda: deque())
        self.rate_limit_lock = threading.Lock()

        self.demo_race_condition = False
        self.delay_requests = True

    def start(self):
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(10)
            print(f"Multithreaded HTTP Server running on http://{self.host}:{self.port}")
            print(f"Serving directory: {self.directory}")
            print(f"Max threads: {self.max_threads}")
            print(f"Rate limit: {self.rate_limit} requests/second per IP")

            while True:
                client_socket, client_address = self.socket.accept()
                print(f"Connection from {client_address}")

                with self.thread_lock:
                    if self.active_threads < self.max_threads:
                        thread = threading.Thread(
                            target=self.handle_client_thread,
                            args=(client_socket, client_address),
                            daemon=True
                        )
                        thread.start()
                        self.active_threads += 1
                        print(f"Started thread {thread.ident}, active threads: {self.active_threads}")
                    else:
                        print(f"Thread pool full, rejecting connection from {client_address}")
                        client_socket.close()

        except KeyboardInterrupt:
            print("\nServer shutting down...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.socket.close()

    def handle_client_thread(self, client_socket, client_address):
        try:
            self.handle_request(client_socket, client_address)
        finally:
            client_socket.close()
            with self.thread_lock:
                self.active_threads -= 1
                print(f"Thread {threading.current_thread().ident} finished, active threads: {self.active_threads}")

    def handle_request(self, client_socket, client_address):
        try:
            client_ip = client_address[0]
            time.sleep(1)
            if not self.check_rate_limit(client_ip):
                self.send_error(client_socket, 429, "Too Many Requests")
                return

            request = client_socket.recv(1024).decode('utf-8')
            if not request:
                return

            lines = request.split('\n')
            if not lines:
                return

            request_line = lines[0].strip()
            parts = request_line.split()
            if len(parts) < 3:
                self.send_error(client_socket, 400, "Bad Request")
                return

            method, path, version = parts

            if method != 'GET':
                self.send_error(client_socket, 405, "Method Not Allowed")
                return

            path = unquote(path)

            if self.delay_requests:
                print(f"Thread {threading.current_thread().ident}: Simulating work for 1 second...")
                time.sleep(1)

            self.serve_file(client_socket, path)

            self.increment_counter(path)

        except Exception as e:
            print(f"Error handling request: {e}")
            self.send_error(client_socket, 500, "Internal Server Error")

    def check_rate_limit(self, client_ip):
        current_time = time.time()

        with self.rate_limit_lock:
            # Clean old requests outside the time window
            client_deque = self.client_requests[client_ip]
            while client_deque and current_time - client_deque[0] > self.rate_limit_window:
                client_deque.popleft()

            # Check if under rate limit
            if len(client_deque) >= self.rate_limit:
                return False

            # Add current request timestamp
            client_deque.append(current_time)
            return True

    def increment_counter(self, path):
        if self.demo_race_condition:
            time.sleep(0.1)
            current_count = self.file_counters[path]
            time.sleep(0.1)
            self.file_counters[path] = current_count + 1
            print(f"Thread {threading.current_thread().ident}: Counter for {path} = {self.file_counters[path]}")
        else:
            with self.counter_lock:
                self.file_counters[path] += 1
                print(f"Thread {threading.current_thread().ident}: Counter for {path} = {self.file_counters[path]}")

    def get_file_counter(self, path):
        with self.counter_lock:
            return self.file_counters[path]

    def serve_file(self, client_socket, path):
        if path == '/':
            path = ''
        else:
            path = path.lstrip('/')

        full_path = os.path.join(self.directory, path)

        if not full_path.startswith(self.directory):
            self.send_error(client_socket, 403, "Forbidden")
            return

        if not os.path.exists(full_path):
            self.send_error(client_socket, 404, "Not Found")
            return

        if os.path.isdir(full_path):
            self.serve_directory(client_socket, full_path, path)
        else:
            self.serve_regular_file(client_socket, full_path)

    def serve_directory(self, client_socket, dir_path, url_path):
        try:
            files = os.listdir(dir_path)
            files.sort()

            html = self.generate_directory_listing(files, url_path)

            response = "HTTP/1.1 200 OK\r\n"
            response += "Content-Type: text/html\r\n"
            response += f"Content-Length: {len(html.encode('utf-8'))}\r\n"
            response += "\r\n"
            response += html

            client_socket.send(response.encode('utf-8'))

        except Exception as e:
            print(f"Error serving directory: {e}")
            self.send_error(client_socket, 500, "Internal Server Error")

    def generate_directory_listing(self, files, url_path):
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Directory listing for /{}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin: 10px 0; }}
        a {{ text-decoration: none; color: #0066cc; }}
        a:hover {{ text-decoration: underline; }}
        .file-icon {{ margin-right: 10px; }}
    </style>
</head>
<body>
    <h1>Directory listing for /{}</h1>
    <ul>
""".format(url_path, url_path)

        if url_path:
            parent_path = '/'.join(url_path.split('/')[:-1]) if '/' in url_path else ''
            html += f'        <li><a href="/{parent_path}">..</a> (parent directory)</li>\n'

        for file in files:
            file_path = os.path.join(self.directory, url_path, file)
            is_dir = os.path.isdir(file_path)

            if url_path:
                link_path = f"/{url_path}/{file}"
            else:
                link_path = f"/{file}"

            if is_dir:
                icon = "[DIR]"
                file_type = "directory"
                request_count = 0  # Don't count directory requests
            else:
                icon = self.get_file_icon(file)
                file_type = "file"
                request_count = self.get_file_counter(link_path)

            html += f'        <li>{icon} <a href="{link_path}">{file}</a> ({file_type}) - <strong>{request_count} requests</strong></li>\n'
        return html

    def get_file_icon(self, filename):
        """Get appropriate icon for file type"""
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.html' or ext == '.htm':
            return "[HTML]"
        elif ext == '.pdf':
            return "[PDF]"
        elif ext == '.png' or ext == '.jpg' or ext == '.jpeg':
            return "[IMG]"
        else:
            return "[FILE]"

    def serve_regular_file(self, client_socket, file_path):
        """Serve a regular file"""
        try:
            # Get file extension and content type
            ext = os.path.splitext(file_path)[1].lower()
            content_type = self.get_content_type(ext)

            # Read file
            with open(file_path, 'rb') as f:
                content = f.read()

            # Send response
            response = "HTTP/1.1 200 OK\r\n"
            response += f"Content-Type: {content_type}\r\n"
            response += f"Content-Length: {len(content)}\r\n"
            response += "\r\n"

            client_socket.send(response.encode('utf-8'))
            client_socket.send(content)

        except Exception as e:
            print(f"Error serving file: {e}")
            self.send_error(client_socket, 500, "Internal Server Error")

    def get_content_type(self, ext):
        content_types = {
            '.html': 'text/html',
            '.png': 'image/png',
            '.pdf': 'application/pdf',
        }
        return content_types.get(ext, 'application/octet-stream')

    def send_error(self, client_socket, code, message):
        """Send HTTP error response"""
        error_messages = {
            400: "Bad Request",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            429: "Too Many Requests",
            500: "Internal Server Error"
        }

        status_message = error_messages.get(code, "Unknown Error")
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{code} {status_message}</title>
</head>
<body>
    <h1>{code} {status_message}</h1>
    <p>{message}</p>
</body>
</html>"""

        response = f"HTTP/1.1 {code} {status_message}\r\n"
        response += "Content-Type: text/html\r\n"
        response += f"Content-Length: {len(html.encode('utf-8'))}\r\n"
        response += "\r\n"
        response += html

        try:
            client_socket.send(response.encode('utf-8'))
        except:
            pass


def main():
    directory = "public"
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist")
        sys.exit(1)

    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a directory")
        sys.exit(1)

    demo_race_condition = "--demo-race" in sys.argv
    no_delay = "--no-delay" in sys.argv

    server = HTTPServer('0.0.0.0', 8080, directory, max_threads=10)
    server.demo_race_condition = demo_race_condition
    server.delay_requests = not no_delay

    if demo_race_condition:
        print("WARNING: Running in race condition demo mode - counters may be incorrect!")
    if no_delay:
        print("Running without request delays")

    server.start()


if __name__ == "__main__":
    main()
