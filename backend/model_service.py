import joblib
import json
import pandas as pd
import numpy as np
import logging
from backend.config import MODEL_PATH, ENCODINGS_PATH, FEATURES_PATH, CITY_CENTERS, DEFAULT_LAT, DEFAULT_LNG
from backend.utils import haversine_distance, calculate_confidence_score, generate_arabic_explanation
from backend.schemas import PredictionRequest, PredictionResponse

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self):
        self.model = None
        self.encodings = None
        self.features = None
        self.load_resources()

    def load_resources(self):
        """
        Load machine learning model, district encodings, and feature list.
        """
        try:
            logger.info(f"Loading predictive model from {MODEL_PATH}...")
            self.model = joblib.load(MODEL_PATH)
            
            logger.info(f"Loading district encodings from {ENCODINGS_PATH}...")
            with open(ENCODINGS_PATH, "r", encoding="utf-8") as f:
                self.encodings = json.load(f)
                
            logger.info(f"Loading features from {FEATURES_PATH}...")
            with open(FEATURES_PATH, "r", encoding="utf-8") as f:
                self.features = json.load(f)
                
            logger.info("All model resources loaded successfully!")
        except Exception as e:
            logger.error(f"Error loading model resources: {str(e)}")
            raise e

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        """
        Takes the property inputs, applies feature engineering, runs prediction,
        and packages the results.
        """
        if self.model is None or self.encodings is None:
            raise RuntimeError("Model resources not loaded. Check server logs.")

        # Map english property types to expected category_text
        # Training categories are: ['بيع', 'دور - بيع', 'شقة - بيع', 'فيلا - بيع']
        category_map = {
            "Villa": "فيلا - بيع",
            "Apartment": "شقة - بيع",
            "Duplex": "دور - بيع",
            "Land": "بيع"
        }
        category_text = category_map.get(request.property_type, "بيع")

        # Map binary metrics for score calculations
        elevator_num = 1.0 if request.elevator else 0.0
        ac_num = 1.0 if request.ac else 0.0
        furnished_num = 1.0 if request.furnished else 0.0
        pool_num = 1.0 if request.pool else 0.0
        
        car_entrance_num = 1.0 if request.car_entrance else 0.0
        basement_num = 1.0 if request.basement else 0.0
        backyard_num = 1.0 if request.yard else 0.0  # Mapped request.yard -> backyard

        # Select city coordinates center dynamically
        city_name = request.city.strip().lower()
        center_lat, center_lng = CITY_CENTERS.get(city_name, (DEFAULT_LAT, DEFAULT_LNG))

        # Feature calculation
        distance_to_center = haversine_distance(
            request.latitude, request.longitude, center_lat, center_lng
        )
        total_rooms = request.bedrooms + request.livings + request.bathrooms
        
        # Avoid division by zero for room spacing calculation
        total_living = float(request.bedrooms + request.livings)
        if total_living == 0.0:
            total_living = 1.0
        space_per_room = request.area / total_living
        
        # Avoid division by zero for bathroom ratio calculation
        beds_divisor = float(request.bedrooms) if request.bedrooms > 0 else 1.0
        bathroom_ratio = float(request.bathrooms) / beds_divisor
        
        luxury_score = elevator_num + ac_num + pool_num + furnished_num
        infra_score = car_entrance_num + basement_num + backyard_num
        
        ketchen_val = 1.0 if request.ketchen else 0.0

        # Construct feature dict matching the exact columns in train_model.py
        raw_data = {
            "area": [request.area],
            "beds": [float(request.bedrooms)],
            "livings": [float(request.livings)],
            "wc": [float(request.bathrooms)],
            "street_width": [request.street_width],
            "age": [request.property_age],
            "location.lat": [request.latitude],
            "location.lng": [request.longitude],
            "distance_to_center": [distance_to_center],
            "space_per_room": [space_per_room],
            "bathroom_ratio": [bathroom_ratio],
            "luxury_score": [luxury_score],
            "total_rooms": [float(total_rooms)],
            "floor number": [float(request.floor_number)],
            "infra_score": [infra_score],
            "ketchen": [ketchen_val],
            "district": [request.district],
            "category_text": [category_text],
        }

        # Convert to Pandas DataFrame
        df = pd.DataFrame(raw_data)

        # Force exact columns list & order based on features.json metadata
        num_features = self.features["num_features"]
        cat_features = self.features["cat_features"]
        input_columns = num_features + cat_features
        df_input = df[input_columns]

        # Call prediction pipeline
        try:
            prediction = self.model.predict(df_input)
            predicted_price = float(prediction[0])
        except Exception as e:
            logger.error(f"XGBoost prediction failed: {str(e)}")
            raise RuntimeError(f"XGBoost model prediction failed: {str(e)}")

        # Ensure predicted price is not negative
        if predicted_price < 0:
            predicted_price = 0.0

        # Calculate price range (90% to 110%)
        min_price = predicted_price * 0.90
        max_price = predicted_price * 1.10

        # Calculate confidence score
        known_districts = self.encodings.get("district_avg_sqm", {})
        confidence = calculate_confidence_score(
            request.area, request.district, distance_to_center, known_districts
        )

        # Generate Arabic explanation
        price_per_sqm = predicted_price / request.area if request.area > 0 else 0.0
        explanation = generate_arabic_explanation(
            request.property_type,
            request.district,
            request.area,
            request.property_age,
            distance_to_center,
            int(luxury_score),
            int(infra_score),
            price_per_sqm
        )

        # Gather summary of features used
        used_features_summary = {
            "distance_to_center_km": round(distance_to_center, 2),
            "luxury_score_out_of_4": int(luxury_score),
            "infra_score_out_of_3": int(infra_score),
            "total_rooms": int(total_rooms),
            "space_per_room_sqm": round(space_per_room, 2),
            "bathroom_ratio": round(bathroom_ratio, 2),
            "mapped_category": category_text
        }

        return PredictionResponse(
            predicted_price=round(predicted_price, 2),
            min_price=round(min_price, 2),
            max_price=round(max_price, 2),
            confidence_score=confidence,
            explanation=explanation,
            used_features=used_features_summary
        )
