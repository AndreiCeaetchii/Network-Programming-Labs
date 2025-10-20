import socket
import os
import sys
import time
from urllib.parse import unquote

class SingleThreadHTTPServer:
    def __init__(self, host='localhost', port=8080, directory='./public'):
        self.host = host
        self.port = port
        self.directory = os.path.abspath(directory)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    def start(self):
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(10)
            print(f"Single-threaded HTTP Server running on http://{self.host}:{self.port}")
            print(f"Serving directory: {self.directory}")
            
            while True:
                client_socket, client_address = self.socket.accept()
                print(f"Connection from {client_address}")
                self.handle_request(client_socket)
                client_socket.close()
                
        except KeyboardInterrupt:
            print("\nServer shutting down...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.socket.close()
    
    def handle_request(self, client_socket):
        try:
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
            
            print("Single-threaded server: Simulating work for 1 second...")
            time.sleep(1)
            
            # Handle the request
            self.serve_file(client_socket, path)
            
        except Exception as e:
            print(f"Error handling request: {e}")
            self.send_error(client_socket, 500, "Internal Server Error")
    
    def serve_file(self, client_socket, path):
        # Remove leading slash and resolve path
        if path == '/':
            path = ''
        else:
            path = path.lstrip('/')
            
        full_path = os.path.join(self.directory, path)
        
        # Security check - ensure path is within served directory
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
            
            # Generate HTML directory listing
            html = self.generate_directory_listing(files, url_path)
            
            # Send response
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
        """Generate HTML directory listing"""
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
        
        # Add parent directory link if not at root
        if url_path:
            parent_path = '/'.join(url_path.split('/')[:-1]) if '/' in url_path else ''
            html += f'        <li><a href="/{parent_path}">..</a> (parent directory)</li>\n'
        
        # Add files and directories
        for file in files:
            file_path = os.path.join(self.directory, url_path, file)
            is_dir = os.path.isdir(file_path)
            
            # Create link path
            if url_path:
                link_path = f"/{url_path}/{file}"
            else:
                link_path = f"/{file}"
                
            # Add file icon and link
            if is_dir:
                icon = "[DIR]"
                file_type = "directory"
            else:
                icon = self.get_file_icon(file)
                file_type = "file"
                
            html += f'        <li>{icon} <a href="{link_path}">{file}</a> ({file_type})</li>\n'
        
        html += """    </ul>
</body>
</html>"""
        
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
        error_messages = {
            400: "Bad Request",
            403: "Forbidden", 
            404: "Not Found",
            405: "Method Not Allowed",
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
    
    server = SingleThreadHTTPServer('0.0.0.0', 8081, directory)
    server.start()

if __name__ == "__main__":
    main()
