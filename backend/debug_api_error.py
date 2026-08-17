import urllib.request
import urllib.error

try:
    res = urllib.request.urlopen("http://127.0.0.1:5000/api/data/filters")
    print("Success:", res.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"HTTP Error Code: {e.code}")
    print(f"HTTP Error Body: {e.read().decode('utf-8')}")
