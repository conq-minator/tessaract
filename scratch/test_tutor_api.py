import urllib.request
import json

headers = {
    'Authorization': 'Bearer rQUSMHvr5MVgVdCH-b8seB7UbRYeykyJYjBzaZeN2Pk',
    'Content-Type': 'application/json'
}

code = 'forr i in range(5):\n    print("hello world")'
error = 'SyntaxError: invalid syntax'

# 1. Hint
req = urllib.request.Request(
    'http://localhost:9701/api/v1/tutor/hint',
    data=json.dumps({'topic': 'python', 'level': 1, 'code': code, 'error': error}).encode(),
    headers=headers
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
print("=== HINT L1 ===")
print("Model used:", resp.get("model_used"))
print("Content:\n", resp.get("content"))

# 2. Explain Error
req = urllib.request.Request(
    'http://localhost:9701/api/v1/tutor/explain-error',
    data=json.dumps({'topic': 'python', 'code': code, 'error': error, 'file_path': 'c:\\vibe coded projects\\tessaract\\scratch\\hello.py'}).encode(),
    headers=headers
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
print("\n=== EXPLAIN ERROR ===")
print("Model used:", resp.get("model_used"))
print("Explanation:\n", resp.get("explanation"))

# 3. Ask Question
req = urllib.request.Request(
    'http://localhost:9701/api/v1/tutor/ask',
    data=json.dumps({'topic': 'python', 'code': code, 'error': error, 'question': 'How can I fix line 1?', 'file_path': 'c:\\vibe coded projects\\tessaract\\scratch\\hello.py'}).encode(),
    headers=headers
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
print("\n=== ASK QUESTION ===")
print("Model used:", resp.get("model_used"))
print("Answer:\n", resp.get("answer"))
