import zlib
import base64
import requests
import json

print("--- Testing Kroki Renderer ---")

# Simple Diagram
simple_code = "graph TD; A-->B;"

def test_kroki(code, compression_type="zlib"):
    print(f"\nTesting with compression: {compression_type}")
    try:
        encoded = ""
        if compression_type == "zlib":
            # Current implementation: zlib.compress (RFC 1950)
            compressed = zlib.compress(code.encode('utf-8'))
            encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
        elif compression_type == "deflate":
            # Raw Deflate (RFC 1951) - like mermaid.ink/pako
            compressor = zlib.compressobj(9, zlib.DEFLATED, -15, 8, zlib.Z_DEFAULT_STRATEGY)
            compressed = compressor.compress(code.encode('utf-8')) + compressor.flush()
            encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
        elif compression_type == "zlib_9":
             # Zlib with max compression
            compressed = zlib.compress(code.encode('utf-8'), 9)
            encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
            
        print(f"Encoded string (first 20): {encoded[:20]}...")
        
        url = f"https://kroki.io/mermaid/png/{encoded}"
        print(f"URL: {url}")
        
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: Image received.")
            print(f"Content Length: {len(response.content)}")
            return True
        else:
            print("FAILURE: API returned error.")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False

# 1. Test current implementation (ZLIB)
print("1. Current Implementation (ZLIB)")
test_kroki(simple_code, "zlib")

# 2. Test Raw Deflate
print("2. Raw Deflate (like mermaid.ink)")
test_kroki(simple_code, "deflate")

# 3. Test Complex Diagram (that user struggled with)
complex_code_mindmap = """mindmap
  root(("Garment Factory"))
    Process("Garment Production")"""
print("\n3. Testing Complex Mindmap (ZLIB)")
test_kroki(complex_code_mindmap, "zlib")

def test_kroki_post(code):
    print(f"\nTesting POST Method")
    try:
        url = "https://kroki.io/mermaid/png"
        print(f"URL: {url}")
        # Send raw code in body
        response = requests.post(url, data=code.encode('utf-8'))
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
             print("SUCCESS: Image received.")
             print(f"Content Length: {len(response.content)}")
             return True
        else:
             print("FAILURE: API returned error.")
             print(f"Response: {response.text}")
             return False
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False

# 4. Test POST with simple code
print("\n4. Testing POST with Simple Code")
test_kroki_post(simple_code)

# 5. Test POST with Complex Code
print("\n5. Testing POST with Complex Mindmap")
test_kroki_post(complex_code_mindmap)
