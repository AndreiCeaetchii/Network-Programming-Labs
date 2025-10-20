import socket
import time
import threading

def make_request(server_host, server_port, user_name, request_num, path="/"):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((server_host, server_port))
        
        request = f"GET {path} HTTP/1.1\r\n"
        request += f"Host: {server_host}:{server_port}\r\n"
        request += "Connection: close\r\n"
        request += f"User-Agent: {user_name}-Request-{request_num}\r\n"
        request += "\r\n"
        
        sock.send(request.encode('utf-8'))
        
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        
        sock.close()
        
        # Parse response
        response_str = response.decode('utf-8', errors='ignore')
        lines = response_str.split('\n')
        status_line = lines[0].strip()
        status_code = int(status_line.split()[1])
        
        return status_code
        
    except Exception as e:
        print(f"Error: {e}")
        return 0

def spam_user(server_host, server_port, duration=10):
    start_time = time.time()
    successful = 0
    rate_limited = 0
    total = 0
    
    while time.time() - start_time < duration:
        status = make_request(server_host, server_port, "SPAM", total, "/")
        
        if status == 200:
            successful += 1
            print(f"Request {total}: Success")
        elif status == 429:
            rate_limited += 1
            print(f"Request {total}: Rate Limited")
        else:
            print(f"Request {total}: Error {status}")
        
        total += 1
        
        # Wait 0.1 seconds (10 requests per second)
        time.sleep(0.1)
    
    print(f"\nSPAM USER RESULTS:")
    print(f"   Total requests: {total}")
    print(f"   Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"   Rate Limited: {rate_limited} ({rate_limited/total*100:.1f}%)")
    print(f"   Success rate: {successful/total*100:.1f}%")
    
    return successful, rate_limited, total

def normal_user(server_host, server_port, duration=10):
    start_time = time.time()
    successful = 0
    rate_limited = 0
    total = 0
    
    while time.time() - start_time < duration:
        status = make_request(server_host, server_port, "NORMAL", total, "/")
        
        if status == 200:
            successful += 1
            print(f"Request {total}: Success")
        elif status == 429:
            rate_limited += 1
            print(f"Request {total}: Rate Limited")
        else:
            print(f"Request {total}: Error {status}")
        
        total += 1
        
        time.sleep(0.25)
    
    print(f"\nNORMAL USER RESULTS:")
    print(f"Total requests: {total}")
    print(f"Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"Rate Limited: {rate_limited} ({rate_limited/total*100:.1f}%)")
    print(f"Success rate: {successful/total*100:.1f}%")
    
    return successful, rate_limited, total

def test_concurrent_users(server_host, server_port, duration=10):
    print("="*60)
    print("🔄 TESTING BOTH USERS CONCURRENTLY")
    print("="*60)
    print(f"Server: {server_host}:{server_port}")
    print(f"Test duration: {duration} seconds")
    print(f"Rate limit: 5 requests/second per IP")
    print("="*60)

    spam_results = [0, 0, 0]
    normal_results = [0, 0, 0]

    def spam_thread():
        nonlocal spam_results
        spam_results = spam_user(server_host, server_port, duration)
    
    def normal_thread():
        nonlocal normal_results
        normal_results = normal_user(server_host, server_port, duration)
    
    spam_t = threading.Thread(target=spam_thread)
    normal_t = threading.Thread(target=normal_thread)
    
    print("\nStarting both users simultaneously...")
    start_time = time.time()
    
    spam_t.start()
    normal_t.start()
    
    spam_t.join()
    normal_t.join()
    
    end_time = time.time()
    
    # Compare results
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)
    
    spam_success_rate = spam_results[0] / spam_results[2] * 100 if spam_results[2] > 0 else 0
    normal_success_rate = normal_results[0] / normal_results[2] * 100 if normal_results[2] > 0 else 0
    
    print(f"SPAM USER:")
    print(f"   Success rate: {spam_success_rate:.1f}%")
    print(f"   Requests blocked: {spam_results[1]} out of {spam_results[2]}")
    
    print(f"\nNORMAL USER:")
    print(f"   Success rate: {normal_success_rate:.1f}%")
    print(f"   Requests blocked: {normal_results[1]} out of {normal_results[2]}")

def main():
    server_host = "localhost"
    server_port = 8080
    
    print(f"Testing server: {server_host}:{server_port}")
    
    try:
        test_concurrent_users(server_host, server_port, 8)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\nTest failed: {e}")

if __name__ == "__main__":
    main()
