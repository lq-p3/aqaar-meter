import urllib.request
import json
import sys

def test_prediction():
    url = "http://localhost:5000/api/predict"
    payload = {
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
    
    headers = {"Content-Type": "application/json"}
    req_data = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
    
    print("⏳ Sending prediction request to ASP.NET Core API Gateway...")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = response.read().decode("utf-8")
            res_json = json.loads(res_data)
            print("✅ ASP.NET Core API Gateway responded successfully!")
            print(f"  - Predicted Price:  SAR {res_json['predicted_price']:,.2f}")
            print(f"  - Min Price:        SAR {res_json['min_price']:,.2f}")
            print(f"  - Max Price:        SAR {res_json['max_price']:,.2f}")
            print(f"  - Confidence Score: {res_json['confidence_score']}%")
            print(f"  - Explanation:      {res_json['explanation']}")
            print(f"  - Used Features:    {json.dumps(res_json['used_features'], ensure_ascii=False)}")
    except urllib.error.URLError as e:
        print(f"❌ Server connection failed: {e}")
        print("Make sure BOTH FastAPI (port 8000) and ASP.NET Core (port 5000) are running.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_prediction()
