#!/usr/bin/env python3
"""
Simple Performance Test
Compares single-threaded vs multithreaded server performance
"""

import socket
import time
import threading

def make_request(server_host, server_port, request_id, timeout=15):
    """Make a single HTTP request"""
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
    """Test server performance with concurrent requests"""
    print(f"\n🧵 Testing {server_name}...")
    print(f"   Making {num_requests} concurrent requests")
    
    start_time = time.time()
    successful = 0
    total_time = 0
    
    # Create threads for concurrent requests
    threads = []
    results = [None] * num_requests
    
    def make_request_thread(request_id):
        success, response_time = make_request(server_host, server_port, request_id)
        results[request_id] = (success, response_time)
    
    # Start all threads
    for i in range(num_requests):
        thread = threading.Thread(target=make_request_thread, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Analyze results
    for result in results:
        if result and result[0]:  # If successful
            successful += 1
    
    throughput = successful / total_time if total_time > 0 else 0
    
    print(f"   ✅ Results:")
    print(f"      Successful: {successful}/{num_requests}")
    print(f"      Total time: {total_time:.2f} seconds")
    print(f"      Throughput: {throughput:.2f} requests/second")
    
    return {
        'successful': successful,
        'total': num_requests,
        'total_time': total_time,
        'throughput': throughput
    }

def main():
    print("⚡ SIMPLE PERFORMANCE COMPARISON")
    print("This test compares single-threaded vs multithreaded servers")
    print()
    
    print("📋 Instructions:")
    print("1. Start your multithreaded server: python server.py")
    print("2. Run this test to see performance")
    print("3. Compare with single-threaded server if available")
    print()
    
    # Test multithreaded server
    print("="*60)
    print("🚀 PERFORMANCE TEST")
    print("="*60)
    
    try:
        # Test multithreaded server (port 8080)
        results = test_server_performance("localhost", 8080, 10, "Multithreaded Server")
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"   Server: Multithreaded")
        print(f"   Requests: {results['successful']}/{results['total']} successful")
        print(f"   Time: {results['total_time']:.2f} seconds")
        print(f"   Throughput: {results['throughput']:.2f} req/s")
        
        print(f"\n🔍 ANALYSIS:")
        if results['total_time'] < 5:
            print(f"   ✅ Good performance! {results['total_time']:.1f}s for 10 requests")
            print(f"   ✅ Requests are being processed concurrently")
        else:
            print(f"   ⚠️  Slow performance: {results['total_time']:.1f}s for 10 requests")
            print(f"   ⚠️  Requests may be processed sequentially")
        
        expected_time = 10  # 10 requests × 1 second delay each
        improvement = (expected_time - results['total_time']) / expected_time * 100
        print(f"   📈 Performance improvement: {improvement:.1f}% vs sequential processing")
        
        print(f"\n💡 EXPECTED BEHAVIOR:")
        print(f"   - Single-threaded: ~10 seconds (sequential)")
        print(f"   - Multithreaded: ~1-2 seconds (concurrent)")
        print(f"   - Your result: {results['total_time']:.1f} seconds")
        
        if results['total_time'] < 3:
            print(f"   🎯 Excellent! Multithreading is working correctly")
        elif results['total_time'] < 6:
            print(f"   ✅ Good! Some concurrency is happening")
        else:
            print(f"   ⚠️  Check if multithreading is implemented correctly")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure your server is running on localhost:8080")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETED")
    print("="*60)

if __name__ == "__main__":
    main()
