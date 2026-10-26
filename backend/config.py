import os
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Model and metadata file paths
MODEL_PATH = os.getenv("MODEL_PATH", os.path.join(BASE_DIR, "backend", "predictive_model.pkl"))
ENCODINGS_PATH = os.getenv("ENCODINGS_PATH", os.path.join(BASE_DIR, "backend", "district_encodings.json"))
FEATURES_PATH = os.getenv("FEATURES_PATH", os.path.join(BASE_DIR, "backend", "features.json"))

# Geospatial centers of cities in Saudi Arabia for distance calculation
CITY_CENTERS = {
    "abha": (18.2164, 42.5053),
    "khamis mushait": (18.3064, 42.7292),
    "khamis": (18.3064, 42.7292),
    "riyadh": (24.7136, 46.6753)
}

# Default center if city not found
DEFAULT_LAT = 18.2164
DEFAULT_LNG = 42.5053

# FastAPI app configurations
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
