# AqaarMeter - Intelligent Real Estate Appraisal System

AqaarMeter is a smart property valuation and appraisal platform tailored for Saudi Arabia (specifically Riyadh and Aseer regions). By leveraging a production-grade machine learning pipeline (built on XGBoost), geospatial intelligence (Leaflet.js mapping, Haversine formula), and detailed building attributes, AqaarMeter delivers high-fidelity real estate valuations and instant professional PDF reports.

## System Architecture

AqaarMeter utilizes a **Hybrid Microservice Architecture** designed for high scalability, type-safe validation, and database audit logging:

1. **Frontend:** Responsive vanilla HTML5/CSS3 application incorporating **Leaflet.js** for location mapping, **jsPDF** for dynamic reporting, and communicating directly with the ASP.NET Core gateway.
2. **API Gateway (ASP.NET Core 8 Web API):** Built inside `/AqaarMeterAPI`. Act as the primary external gateway (port `5000`) for all frontend operations:
   - Accepts valuation requests, runs model-state validations.
   - Forwards predictions to the Python ML microservice.
   - Logs valuation transactions to a local **SQLite database (`appraisals.db`)** using Entity Framework Core (EF Core).
   - Serves appraisal transaction history.
3. **ML Microservice (Python FastAPI):** Built inside `/backend`. Runs on port `8000`:
   - Loads the XGBoost regressor model (`predictive_model.pkl`).
   - Conducts identical feature engineering to model training (Haversine calculations, room space ratios, luxury/infra scoring).
   - Generates natural language Arabic valuation summaries.

---

## Getting Started

To run the full stack locally, you need to run **both** the Python ML microservice and the ASP.NET Core API Gateway.

### Prerequisites
- Python 3.9+
- .NET 8.0 SDK

---

### Step 1: Run the Python ML Microservice (Port 8000)

1. **Activate Virtual Environment:**
   Navigate to the project root directory and activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```
2. **Launch the FastAPI Server:**
   ```bash
   uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
   *FastAPI will listen at `http://127.0.0.1:8000`.*

---

### Step 2: Run the ASP.NET Core Gateway (Port 5000)

1. **Navigate to the API project folder:**
   ```bash
   cd AqaarMeterAPI
   ```
2. **Build and Run the C# project:**
   ```bash
   dotnet run --launch-profile http
   ```
   *ASP.NET Core will listen at `http://localhost:5000`. On startup, it will automatically create the SQLite database `appraisals.db` in its folder if it does not exist.*

---

### Step 3: Launch Frontend

Open `service3.html` directly in your browser.
To serve it through a clean local web server to avoid CORS/origin warnings on some browsers:
```bash
python3 -m http.server 3000
```
Then navigate to: [http://localhost:3000/service3.html](http://localhost:3000/service3.html)

---

## API Specifications (ASP.NET Core Gateway)

### 1. `POST /api/predict`
Submit property configurations to get market valuation metrics.
- **URL:** `http://localhost:5000/api/predict`
- **Method:** `POST`
- **Payload Request Schema:**
  ```json
  {
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
    "elevator": true,
    "ac": true,
    "furnished": true,
    "pool": true,
    "car_entrance": true,
    "basement": true,
    "yard": true,
    "livings": 2,
    "floor_number": 0,
    "ketchen": true
  }
  ```
- **JSON Output Schema:**
  ```json
  {
    "predicted_price": 1679930.62,
    "min_price": 1511937.56,
    "max_price": 1847923.69,
    "confidence_score": 85.0,
    "explanation": "تم احتساب التقييم التقديري بناءً على تحليل مقارن للسوق العقاري...",
    "used_features": {
      "distance_to_center_km": 3.41,
      "luxury_score_out_of_4": 4,
      "infra_score_out_of_3": 3,
      "total_rooms": 11,
      "space_per_room_sqm": 64.29,
      "bathroom_ratio": 0.8,
      "mapped_category": "فيلا - بيع"
    }
  }
  ```

### 2. `GET /api/predict/history`
Retrieve the last 10 appraisal queries logged in the SQLite database.
- **URL:** `http://localhost:5000/api/predict/history?limit=10`
- **Method:** `GET`
