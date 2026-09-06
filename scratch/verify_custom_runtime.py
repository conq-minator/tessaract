import urllib.request
import json

headers = {
    'Authorization': 'Bearer rQUSMHvr5MVgVdCH-b8seB7UbRYeykyJYjBzaZeN2Pk',
    'Content-Type': 'application/json'
}

# Test 1: Python runtime IndexError in arbitrary code
code_snippet = "names = ['Alice', 'Bob']\nprint(names[5])"
error_str = "IndexError: list index out of range"

req = urllib.request.Request(
    'http://localhost:9701/api/v1/tutor/explain-error',
    data=json.dumps({'topic': 'python', 'code': code_snippet, 'error': error_str}).encode(),
    headers=headers
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
print("=== RUNTIME ERROR EXPLANATION ===")
print("Model:", resp.get("model_used"))
print("Explanation:", resp.get("explanation"))
assert "file location" not in resp.get("explanation", "").lower()
assert "indexerror" in resp.get("explanation", "").lower() or "index" in resp.get("explanation", "").lower()

# Test 2: Level 1 Hint on custom runtime error
req = urllib.request.Request(
    'http://localhost:9701/api/v1/tutor/hint',
    data=json.dumps({'topic': 'python', 'level': 1, 'code': code_snippet, 'error': error_str}).encode(),
    headers=headers
)
resp_h1 = json.loads(urllib.request.urlopen(req).read().decode())
print("\n=== RUNTIME HINT L1 ===")
print("Model:", resp_h1.get("model_used"))
print("Content:", resp_h1.get("content"))
assert "```" not in resp_h1.get("content", "")

print("\n=== ALL RUNTIME CHECKS PASSED ===")
