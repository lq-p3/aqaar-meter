from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from backend.schemas import PredictionRequest, PredictionResponse
from backend.model_service import ModelService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("backend")

# Global model service instance
model_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_service
    logger.info("Starting up AqaarMeter FastAPI application...")
    try:
        model_service = ModelService()
        logger.info("FastAPI backend resources loaded successfully.")
    except Exception as e:
        logger.critical(f"Failed to load model resources on startup: {str(e)}")
        # We allow application to start so that health endpoint can report error
    yield
    logger.info("Shutting down AqaarMeter FastAPI application...")

app = FastAPI(
    title="AqaarMeter Real Estate Valuation API",
    description="Production-Ready API connecting XGBoost predictions to frontend AqaarMeter application",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for local development access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Verify backend and model health."""
    if model_service is not None and model_service.model is not None:
        return {"status": "healthy", "model_loaded": True}
    return {"status": "unhealthy", "model_loaded": False}

@app.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
def predict_price(request: PredictionRequest):
    """
    Predict property price using XGBoost Regressor model.
    """
    logger.info(f"Received prediction request for city={request.city}, district={request.district}, area={request.area}")
    
    if model_service is None or model_service.model is None:
        logger.error("Prediction request failed: Model service resources are not initialized.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model is currently unavailable. Please verify that predictive_model.pkl is present."
        )

    try:
        response = model_service.predict(request)
        logger.info(f"Successful prediction: SAR {response.predicted_price:,.2f}")
        return response
    except Exception as e:
        logger.error(f"Error executing prediction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prediction error: {str(e)}"
        )
