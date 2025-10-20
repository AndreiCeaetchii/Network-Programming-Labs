#!/usr/bin/env python3
"""
Simple Rate Limiting Test
Tests the rate limiting feature with two simulated users:
- Friend 1: Spams requests (should get rate limited)
- Friend 2: Sends requests just below rate limit (should succeed)
"""

import socket
import time
import threading

def make_request(server_host, server_port, user_name, request_num, path="/"):
    """Make a single HTTP request"""
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
    """Simulate a user spamming requests (10 requests/second)"""
    print(f"\n🚨 SPAM USER: Starting spam attack for {duration} seconds...")
    print("   Sending 10 requests per second (above 5 req/s limit)")
    
    start_time = time.time()
    successful = 0
    rate_limited = 0
    total = 0
    
    while time.time() - start_time < duration:
        # Make request
        status = make_request(server_host, server_port, "SPAM", total, "/")
        
        if status == 200:
            successful += 1
            print(f"   ✅ Request {total}: Success")
        elif status == 429:
            rate_limited += 1
            print(f"   🚫 Request {total}: Rate Limited")
        else:
            print(f"   ⚠️  Request {total}: Error {status}")
        
        total += 1
        
        # Wait 0.1 seconds (10 requests per second)
        time.sleep(0.1)
    
    print(f"\n📊 SPAM USER RESULTS:")
    print(f"   Total requests: {total}")
    print(f"   Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"   Rate Limited: {rate_limited} ({rate_limited/total*100:.1f}%)")
    print(f"   Success rate: {successful/total*100:.1f}%")
    
    return successful, rate_limited, total

def normal_user(server_host, server_port, duration=10):
    """Simulate a normal user (4 requests/second - just below limit)"""
    print(f"\n👤 NORMAL USER: Starting normal usage for {duration} seconds...")
    print("   Sending 4 requests per second (below 5 req/s limit)")
    
    start_time = time.time()
    successful = 0
    rate_limited = 0
    total = 0
    
    while time.time() - start_time < duration:
        # Make request
        status = make_request(server_host, server_port, "NORMAL", total, "/")
        
        if status == 200:
            successful += 1
            print(f"   ✅ Request {total}: Success")
        elif status == 429:
            rate_limited += 1
            print(f"   🚫 Request {total}: Rate Limited")
        else:
            print(f"   ⚠️  Request {total}: Error {status}")
        
        total += 1
        
        # Wait 0.25 seconds (4 requests per second)
        time.sleep(0.25)
    
    print(f"\n📊 NORMAL USER RESULTS:")
    print(f"   Total requests: {total}")
    print(f"   Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"   Rate Limited: {rate_limited} ({rate_limited/total*100:.1f}%)")
    print(f"   Success rate: {successful/total*100:.1f}%")
    
    return successful, rate_limited, total

def test_concurrent_users(server_host, server_port, duration=10):
    """Test both users at the same time"""
    print("="*60)
    print("🔄 TESTING BOTH USERS CONCURRENTLY")
    print("="*60)
    print(f"Server: {server_host}:{server_port}")
    print(f"Test duration: {duration} seconds")
    print(f"Rate limit: 5 requests/second per IP")
    print("="*60)
    
    # Start both users in separate threads
    spam_results = [0, 0, 0]  # successful, rate_limited, total
    normal_results = [0, 0, 0]
    
    def spam_thread():
        nonlocal spam_results
        spam_results = spam_user(server_host, server_port, duration)
    
    def normal_thread():
        nonlocal normal_results
        normal_results = normal_user(server_host, server_port, duration)
    
    # Start threads
    spam_t = threading.Thread(target=spam_thread)
    normal_t = threading.Thread(target=normal_thread)
    
    print("\n⏰ Starting both users simultaneously...")
    start_time = time.time()
    
    spam_t.start()
    normal_t.start()
    
    spam_t.join()
    normal_t.join()
    
    end_time = time.time()
    
    # Compare results
    print("\n" + "="*60)
    print("📈 COMPARISON RESULTS")
    print("="*60)
    
    spam_success_rate = spam_results[0] / spam_results[2] * 100 if spam_results[2] > 0 else 0
    normal_success_rate = normal_results[0] / normal_results[2] * 100 if normal_results[2] > 0 else 0
    
    print(f"🔴 SPAM USER:")
    print(f"   Success rate: {spam_success_rate:.1f}%")
    print(f"   Requests blocked: {spam_results[1]} out of {spam_results[2]}")
    
    print(f"\n🟢 NORMAL USER:")
    print(f"   Success rate: {normal_success_rate:.1f}%")
    print(f"   Requests blocked: {normal_results[1]} out of {normal_results[2]}")
    
    print(f"\n🎯 RATE LIMITING EFFECTIVENESS:")
    if normal_success_rate > spam_success_rate:
        print(f"   ✅ Rate limiting is working!")
        print(f"   Normal users get {normal_success_rate - spam_success_rate:.1f}% better success rate")
    else:
        print(f"   ⚠️  Rate limiting may need adjustment")
    
    total_blocked = spam_results[1] + normal_results[1]
    total_requests = spam_results[2] + normal_results[2]
    blocking_rate = total_blocked / total_requests * 100 if total_requests > 0 else 0
    
    print(f"   Overall blocking rate: {blocking_rate:.1f}% ({total_blocked}/{total_requests})")

def main():
    print("🛡️  SIMPLE RATE LIMITING TEST")
    print("This test simulates two friends:")
    print("- Friend 1: Spams requests (should get blocked)")
    print("- Friend 2: Normal usage (should work fine)")
    print()
    
    server_host = "localhost"
    server_port = 8080
    
    print(f"Testing server: {server_host}:{server_port}")
    print("Make sure your multithreaded server is running!")
    print()
    
    try:
        # Test both users concurrently
        test_concurrent_users(server_host, server_port, 8)
        
        print("\n" + "="*60)
        print("✅ TEST COMPLETED")
        print("="*60)
        print("Expected results:")
        print("- Spam user: ~50% success rate")
        print("- Normal user: ~100% success rate")
        print("- Rate limiting should protect normal users from spammers")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main()
