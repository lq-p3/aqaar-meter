import urllib.request
import urllib.error
import json
import sys
import time

def test_full_pipeline():
    base_url = "http://localhost:5000"
    
    # 1. Register User
    print("1. ⏳ Testing Registration Endpoint...")
    reg_url = f"{base_url}/api/auth/register"
    reg_payload = {
        "username": f"testuser_{int(time.time())}",
        "email": f"test_{int(time.time())}@aqaarmeter.com",
        "password": "SecurePassword123",
        "role": "User"
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        req = urllib.request.Request(
            reg_url, 
            data=json.dumps(reg_payload).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
            token = res["token"]
            print("   ✅ User Registered & Logged In Auto-Successfully!")
            print(f"   Username: {res['username']} | Role: {res['role']}")
    except Exception as e:
        print(f"   ❌ Registration Failed: {e}")
        sys.exit(1)

    # 2. Login User
    print("\n2. ⏳ Testing Login Endpoint...")
    login_url = f"{base_url}/api/auth/login"
    login_payload = {
        "usernameOrEmail": reg_payload["username"],
        "password": reg_payload["password"]
    }
    try:
        req = urllib.request.Request(
            login_url, 
            data=json.dumps(login_payload).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
            token = res["token"]
            print("   ✅ User Logged In Successfully!")
            print(f"   Retrieved JWT Token: {token[:30]}...")
    except Exception as e:
        print(f"   ❌ Login Failed: {e}")
        sys.exit(1)

    # 3. Authorized Valuation Prediction
    print("\n3. ⏳ Testing Authorized Prediction Endpoint...")
    predict_url = f"{base_url}/api/predict"
    predict_payload = {
        "city": "Abha",
        "district": "حي المنسك",
        "area": 450.0,
        "bedrooms": 5,
        "bathrooms": 4,
        "property_age": 3.0,
        "street_width": 15.0,
        "property_type": "Villa",
        "latitude": 18.2465,
        "longitude": 42.5117,
        "elevator": True,
        "ac": True,
        "furnished": True,
        "pool": True,
        "car_entrance": True,
        "basement": True,
        "yard": True,
        "livings": 2,
        "floor_number": 0,
        "ketchen": True
    }
    
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    try:
        req = urllib.request.Request(
            predict_url, 
            data=json.dumps(predict_payload).encode("utf-8"), 
            headers=auth_headers, 
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
            print("   ✅ Authorized Prediction succeeded!")
            print(f"   Predicted Price: SAR {res['predicted_price']:,.2f}")
            print(f"   Confidence Score: {res['confidence_score']}%")
    except Exception as e:
        print(f"   ❌ Authorized Prediction Failed: {e}")
        sys.exit(1)

    # 4. View User Appraisal History
    print("\n4. ⏳ Testing History Endpoint (Authorized)...")
    history_url = f"{base_url}/api/predict/history?limit=5"
    try:
        req = urllib.request.Request(history_url, headers=auth_headers, method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
            print(f"   ✅ History retrieved successfully! Found {len(res)} logs.")
            for log in res:
                print(f"     - Log ID: {log['id']} | Timestamp: {log['timestamp']} | Predicted: SAR {log['predictedPrice']:,.2f}")
    except Exception as e:
        print(f"   ❌ History Fetch Failed: {e}")
        sys.exit(1)

    # 5. Nearby Transactions Search (CMA)
    print("\n5. ⏳ Testing Spatial Nearby Transactions (CMA)...")
    nearby_url = f"{base_url}/api/predict/nearby?lat=18.2465&lng=42.5117&radiusKm=5&limit=3"
    try:
        req = urllib.request.Request(nearby_url, headers=auth_headers, method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
            print(f"   ✅ Nearby transactions found: {len(res)}")
            for tx in res:
                print(f"     - Sale ID: {tx['id']} | Price: SAR {tx['price']:,.2f} | Distance: {tx['distance_km']} km | District: {tx['district']}")
    except Exception as e:
        print(f"   ❌ Nearby Transactions Failed: {e}")
        sys.exit(1)

    # 6. District Trends Analytics
    print("\n6. ⏳ Testing District Analytics & Trends...")
    trends_url = f"{base_url}/api/analytics/trends?district=%D8%AD%D9%8A%20%D8%A7%D9%84%D9%85%D9%86%D8%B3%D9%83" # encoded "حي المنسك"
    try:
        req = urllib.request.Request(trends_url, headers=auth_headers, method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
            print(f"   ✅ Market Trends calculated for {res['district']}!")
            print(f"     - Total Transactions: {res['totalTransactions']}")
            print(f"     - Avg Price per SQM:  SAR {res['averagePricePerSqm']:,.2f}/sqm")
            print("     - Avg by Property Types:")
            for pt in res['byPropertyType']:
                print(f"       * {pt['propertyType']}: SAR {pt['averagePricePerSqm']:,.2f}/sqm (Vol: {pt['volume']})")
    except Exception as e:
        print(f"   ❌ Analytics trends failed: {e}")
        sys.exit(1)

    print("\n🏆 Integration Testing Complete: ALL ENDPOINTS ARE FULLY OPERATIONAL!")

if __name__ == "__main__":
    test_full_pipeline()
