from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional

class PredictionRequest(BaseModel):
    city: str = Field(..., description="City name (e.g., Abha, Khamis Mushait, Riyadh)")
    district: str = Field(..., description="District name in Arabic (e.g., حي المنسك)")
    area: float = Field(..., description="Total building/land area in square meters")
    bedrooms: int = Field(..., description="Number of bedrooms")
    bathrooms: int = Field(..., description="Number of bathrooms/WCs")
    property_age: float = Field(..., description="Age of the property in years")
    street_width: float = Field(..., description="Width of the street in front of the property in meters")
    property_type: str = Field(..., description="Type of property (Villa, Apartment, Duplex, Land)")
    latitude: float = Field(..., description="Geographical latitude coordinate")
    longitude: float = Field(..., description="Geographical longitude coordinate")
    elevator: bool = Field(False, description="Whether the property has an elevator")
    ac: bool = Field(False, description="Whether the property has air conditioning")
    furnished: bool = Field(False, description="Whether the property is furnished")
    pool: bool = Field(False, description="Whether the property has a swimming pool")
    car_entrance: bool = Field(False, description="Whether the property has a dedicated car entrance")
    basement: bool = Field(False, description="Whether the property has a basement")
    yard: bool = Field(False, description="Whether the property has a yard/backyard")

    # Optional extra features that are useful but not strictly mandatory (defaulted)
    livings: int = Field(1, description="Number of living rooms")
    floor_number: int = Field(0, description="Floor number of the property")
    ketchen: bool = Field(True, description="Whether the property has a kitchen")

    @field_validator('area')
    def validate_area(cls, v):
        if v <= 0:
            raise ValueError("Area must be greater than 0")
        if v > 10000:
            raise ValueError("Area seems unrealistically large (> 10,000 sqm)")
        return v

    @field_validator('bedrooms', 'bathrooms', 'livings')
    def validate_non_negative_rooms(cls, v, info):
        if v < 0:
            raise ValueError(f"{info.field_name} count cannot be negative")
        if v > 50:
            raise ValueError(f"{info.field_name} count seems unrealistically large (> 50)")
        return v

    @field_validator('property_age', 'street_width')
    def validate_non_negative_metrics(cls, v, info):
        if v < 0:
            raise ValueError(f"{info.field_name} cannot be negative")
        return v

    @field_validator('latitude')
    def validate_latitude(cls, v):
        if not (-90.0 <= v <= 90.0):
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator('longitude')
    def validate_longitude(cls, v):
        if not (-180.0 <= v <= 180.0):
            raise ValueError("Longitude must be between -180 and 180")
        return v


class PredictionResponse(BaseModel):
    predicted_price: float = Field(..., description="Estimated market value in SAR")
    min_price: float = Field(..., description="Lower bound value (90% of prediction)")
    max_price: float = Field(..., description="Upper bound value (110% of prediction)")
    confidence_score: float = Field(..., description="Valuation confidence level (percentage, e.g. 85.5)")
    explanation: str = Field(..., description="Natural language explanation of the valuation in Arabic")
    used_features: Dict[str, Any] = Field(..., description="The processed features fed to the model")
