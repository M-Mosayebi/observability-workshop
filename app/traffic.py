import random
import time

import requests

BASE = "http://localhost:5000"
ENDPOINTS = ["/", "/products", "/checkout", "/search"]
# وزن‌ها: checkout و products بیشتر از بقیه صدا زده می‌شوند
WEIGHTS = [1, 4, 3, 2]

print("Sending traffic... (Ctrl+C to stop)")
count = 0
while True:
    path = random.choices(ENDPOINTS, weights=WEIGHTS)[0]
    try:
        r = requests.get(BASE + path, timeout=10)
        count += 1
        if count % 20 == 0:
            print(f"{count} requests sent")
    except Exception as e:
        print("error:", e)
    time.sleep(random.uniform(0.1, 0.5))
