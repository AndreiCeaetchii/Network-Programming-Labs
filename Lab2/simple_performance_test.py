import socket
import time
import threading

def make_request(server_host, server_port, request_id, timeout=15):
    start_time = time.time()
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((server_host, server_port))
        
        request = f"GET / HTTP/1.1\r\n"
        request += f"Host: {server_host}:{server_port}\r\n"
        request += "Connection: close\r\n"
        request += f"User-Agent: Perf-Test-{request_id}\r\n"
        request += "\r\n"
        
        sock.send(request.encode('utf-8'))
        
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        
        end_time = time.time()
        response_time = end_time - start_time
        
        sock.close()
        
        # Parse status code
        response_str = response.decode('utf-8', errors='ignore')
        lines = response_str.split('\n')
        status_line = lines[0].strip()
        status_code = int(status_line.split()[1])
        
        return status_code == 200, response_time
        
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        return False, response_time

def test_server_performance(server_host, server_port, num_requests=10, server_name="Server"):
    start_time = time.time()
    successful = 0
    total_time = 0
    
    threads = []
    results = [None] * num_requests
    
    def make_request_thread(request_id):
        success, response_time = make_request(server_host, server_port, request_id)
        results[request_id] = (success, response_time)
    
    for i in range(num_requests):
        thread = threading.Thread(target=make_request_thread, args=(i,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    for result in results:
        if result and result[0]:
            successful += 1

    print(f"Results:")
    print(f"Successful: {successful}/{num_requests}")
    print(f"Total time: {total_time:.2f} seconds")

    return {
        'successful': successful,
        'total': num_requests,
        'total_time': total_time,
    }

def main():
    try:
        test_server_performance("localhost", 8080, 10, "Multithreaded Server")
        test_server_performance("localhost", 8081, 10, "Single-threaded Server")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    main()
