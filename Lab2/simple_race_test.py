import socket
import time
import threading

def make_request(server_host, server_port, request_id):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((server_host, server_port))

        request = f"GET /pdf1.pdf HTTP/1.1\r\n"
        request += f"Host: {server_host}:{server_port}\r\n"
        request += "Connection: close\r\n"
        request += f"User-Agent: Race-Test-{request_id}\r\n"
        request += "\r\n"

        sock.send(request.encode('utf-8'))

        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk

        sock.close()
        return True

    except Exception as e:
        print(f"Request {request_id} failed: {e}")
        return False

def test_race_condition(server_host, server_port, num_requests=20):
    print("RACE CONDITION TEST")
    print(f"Server: {server_host}:{server_port}")
    print(f"Making {num_requests} concurrent requests")

    print(f"\nSending {num_requests} requests simultaneously...")

    start_time = time.time()

    threads = []
    for i in range(num_requests):
        thread = threading.Thread(target=make_request, args=(server_host, server_port, i))
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    end_time = time.time()

    print(f"\nAll {num_requests} requests completed in {end_time - start_time:.2f} seconds")

def main():
    server_host = "localhost"
    server_port = 8080

    print(f"Testing server: {server_host}:{server_port}")
    print("\nIMPORTANT: Start your server in the right mode!")
    print("\nFor race condition demo:")
    print("  python server.py --demo-race --no-delay")
    print("\nFor normal operation:")
    print("  python server.py --no-delay")
    print()

    try:
        test_race_condition(server_host, server_port, 20)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\nTest failed: {e}")

if __name__ == "__main__":
    main()
