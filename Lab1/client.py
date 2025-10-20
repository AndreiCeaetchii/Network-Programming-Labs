import socket
import sys
import os

class HTTPClient:
    def __init__(self):
        self.socket = None

    def download_file(self, server_host, server_port, filename, save_directory):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((server_host, server_port))

            request = f"GET /{filename} HTTP/1.1\r\nHost: {server_host}:{server_port}\r\nConnection: close\r\n\r\n"
            self.socket.send(request.encode('utf-8'))

            # Receive response
            response = b""
            while True:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                response += chunk

            print(f"Received {len(response)} bytes from server")

            # Split headers and body
            header_end = response.find(b"\r\n\r\n")
            if header_end == -1:
                print("Invalid HTTP response format")
                return False

            header_bytes = response[:header_end].decode("utf-8", errors="ignore")
            body = response[header_end + 4:]

            # Parse headers
            lines = header_bytes.split("\n")
            status_line = lines[0].strip()
            parts = status_line.split()
            status_code = int(parts[1])
            if status_code != 200:
                print(f"Server returned status {status_code}")
                return False

            headers = {}
            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip().lower()] = value.strip()

            content_type = headers.get("content-type", "")
            if "text/html" in content_type:
                print(body.decode("utf-8", errors="ignore"))
            else:
                # Save binary data
                os.makedirs(save_directory, exist_ok=True)
                file_path = os.path.join(save_directory, os.path.basename(filename))
                with open(file_path, "wb") as f:
                    f.write(body)
                print(f"File saved: {file_path}")
                print(f"File size: {len(body)} bytes")

            return True

        except Exception as e:
            print(f"Error downloading file: {e}")
            return False

        finally:
            if self.socket:
                self.socket.close()

    def handle_html_response(self, response, header_end):
        """Handle HTML response - print body as-is"""
        try:
            # Find the start of the body
            response_str = response.decode('utf-8', errors='ignore')
            lines = response_str.split('\n')
            
            # Get the body content
            body_lines = lines[header_end + 1:]
            body = '\n'.join(body_lines)
            
            # Print the HTML body
            print(body)
            
        except Exception as e:
            print(f"Error handling HTML response: {e}")
    
    def handle_binary_response(self, response, header_end, filename, save_directory, content_type):
        """Handle binary response - save file to directory"""
        try:
            # Ensure save directory exists
            os.makedirs(save_directory, exist_ok=True)
            
            # Find the start of the body by looking for the double CRLF
            response_bytes = response
            header_end_bytes = response_bytes.find(b'\r\n\r\n')
            if header_end_bytes == -1:
                # Try single LF
                header_end_bytes = response_bytes.find(b'\n\n')
            
            if header_end_bytes == -1:
                raise Exception("Could not find header end")
            
            # Get the body content (binary data)
            body_data = response_bytes[header_end_bytes + 4:]  # Skip \r\n\r\n
            
            # Determine file extension based on content type
            if 'image/png' in content_type:
                file_ext = '.png'
            elif 'application/pdf' in content_type:
                file_ext = '.pdf'
            else:
                file_ext = ''
            
            # Create filename, handling nested paths
            if '/' in filename:
                # Extract just the filename from the path
                base_name = os.path.splitext(os.path.basename(filename))[0]
            else:
                base_name = os.path.splitext(filename)[0]
            
            if not base_name:
                base_name = 'downloaded_file'
            
            save_filename = base_name + file_ext
            save_path = os.path.join(save_directory, save_filename)
            
            # Save the file
            with open(save_path, 'wb') as f:
                f.write(body_data)
            
            print(f"File saved: {save_path}")
            print(f"File size: {len(body_data)} bytes")
            
        except Exception as e:
            print(f"Error saving binary file: {e}")
    
    def get_directory_listing(self, server_host, server_port, path=''):
        """Get directory listing from server"""
        try:
            # Create socket connection
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((server_host, server_port))
            
            # Create HTTP request
            request_path = f"/{path}" if path else "/"
            request = f"GET {request_path} HTTP/1.1\r\n"
            request += f"Host: {server_host}:{server_port}\r\n"
            request += "Connection: close\r\n"
            request += "\r\n"
            
            # Send request
            self.socket.send(request.encode('utf-8'))
            
            # Receive response
            response = self.socket.recv(4096)
            if not response:
                print("No response received")
                return False
            
            # Parse and display response
            response_str = response.decode('utf-8')
            lines = response_str.split('\n')
            
            # Parse status line
            status_line = lines[0].strip()
            status_parts = status_line.split()
            if len(status_parts) < 3:
                print("Invalid response format")
                return False
            
            status_code = int(status_parts[1])
            
            if status_code == 404:
                print(f"Path not found: {path}")
                return False
            elif status_code != 200:
                print(f"Server error: {status_code}")
                return False
            
            # Print the HTML directory listing
            self.handle_html_response(response, 0)
            return True
            
        except Exception as e:
            print(f"Error getting directory listing: {e}")
            return False
        finally:
            if self.socket:
                self.socket.close()

def main():
    if len(sys.argv) != 4:
        print("Usage: python client.py <server_host> <server_port> <filename>")
        print("Example: python client.py localhost 8080 index.html")
        print("For directory listing, use empty string: python client.py localhost 8080 \"\"")
        sys.exit(1)
    
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    filename = sys.argv[3]
    
    # Default save directory
    save_directory = "downloads"

    client = HTTPClient()
    
    # Check if it's a directory listing request
    if filename == "" or filename == "/":
        success = client.get_directory_listing(server_host, server_port)
    else:
        success = client.download_file(server_host, server_port, filename, save_directory)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
