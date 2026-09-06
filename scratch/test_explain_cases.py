import urllib.request
import json

headers = {
    'Authorization': 'Bearer rQUSMHvr5MVgVdCH-b8seB7UbRYeykyJYjBzaZeN2Pk',
    'Content-Type': 'application/json'
}

# Test 1: What if error passed to explain-error was python file not found?
req = urllib.request.Request(
    'http://localhost:9701/api/v1/tutor/explain-error',
    data=json.dumps({
        'topic': 'python',
        'code': 'def recurse(n):\n    return recurse(n - 1)',
        'error': "python: can't open file 'c:\\vibe coded projects\\tessaract\\scratch\\hello.py': [Errno 2] No such file or directory",
        'file_path': 'c:\\vibe coded projects\\tessaract\\scratch\\hello.py'
    }).encode(),
    headers=headers
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
print("=== TEST 1 (can't open file passed) ===")
print("Model used:", resp.get("model_used"))
print("Explanation:\n", resp.get("explanation"))

# Test 2: What if error passed was a custom runtime error with file_path?
req = urllib.request.Request(
    'http://localhost:9701/api/v1/tutor/explain-error',
    data=json.dumps({
        'topic': 'python',
        'code': 'x = None\nprint(x.value)',
        'error': 'AttributeError: NoneType object has no attribute value',
        'file_path': 'c:\\vibe coded projects\\tessaract\\scratch\\hello.py'
    }).encode(),
    headers=headers
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
print("\n=== TEST 2 (runtime AttributeError) ===")
print("Model used:", resp.get("model_used"))
print("Explanation:\n", resp.get("explanation"))

# Test 3: What if error is not recognized by hardcoded list, falling back to LLM?
req = urllib.request.Request(
    'http://localhost:9701/api/v1/tutor/explain-error',
    data=json.dumps({
        'topic': 'python',
        'code': 'data = {"a": 1}\nprint(data["b"])',
        'error': 'Unexpected custom database error on lookup',
        'file_path': 'c:\\vibe coded projects\\tessaract\\scratch\\hello.py'
    }).encode(),
    headers=headers
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
print("\n=== TEST 3 (novel error to LLM with file_path) ===")
print("Model used:", resp.get("model_used"))
print("Explanation:\n", resp.get("explanation"))
