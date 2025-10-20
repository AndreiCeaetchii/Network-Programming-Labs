#!/usr/bin/env python3
"""
Simple Race Condition Test
Shows the difference between synchronized and unsynchronized counters
"""

import socket
import time
import threading

def make_request(server_host, server_port, request_id):
    """Make a request to increment the counter"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((server_host, server_port))
        
        request = f"GET / HTTP/1.1\r\n"
        request += f"Host: {server_host}:{server_port}\r\n"
        request += "Connection: close\r\n"
        request += f"User-Agent: Race-Test-{request_id}\r\n"
        request += "\r\n"
        
        sock.send(request.encode('utf-8'))
        
        # Just read the response (we don't need the content)
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
    """Test race condition with concurrent requests"""
    print("="*50)
    print("🔬 RACE CONDITION TEST")
    print("="*50)
    print(f"Server: {server_host}:{server_port}")
    print(f"Making {num_requests} concurrent requests")
    print("="*50)
    
    print(f"\n🚀 Sending {num_requests} requests simultaneously...")
    
    start_time = time.time()
    
    # Create threads for concurrent requests
    threads = []
    for i in range(num_requests):
        thread = threading.Thread(target=make_request, args=(server_host, server_port, i))
        threads.append(thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    
    print(f"\n✅ All {num_requests} requests completed in {end_time - start_time:.2f} seconds")
    print("\n📊 Check your server logs to see the counter values!")
    print("   Look for lines like: 'Counter for / = X'")
    print("\n🔍 What to look for:")
    print("   - WITHOUT synchronization: Counter values may be wrong")
    print("   - WITH synchronization: Counter values should be correct")
    print("   - Race condition: Multiple threads show same counter value")

def main():
    print("🔬 SIMPLE RACE CONDITION TEST")
    print("This test shows how threads can interfere with shared data")
    print()
    
    server_host = "localhost"
    server_port = 8080
    
    print(f"Testing server: {server_host}:{server_port}")
    print("\n⚠️  IMPORTANT: Start your server in the right mode!")
    print("\nFor race condition demo:")
    print("  python server.py --demo-race --no-delay")
    print("\nFor normal operation:")
    print("  python server.py --no-delay")
    print()
    
    try:
        # Test with 20 concurrent requests
        test_race_condition(server_host, server_port, 20)
        
        print("\n" + "="*50)
        print("✅ TEST COMPLETED")
        print("="*50)
        print("Compare the results:")
        print("1. Run with --demo-race (no synchronization)")
        print("2. Run without --demo-race (with synchronization)")
        print("3. See the difference in counter accuracy!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main()
