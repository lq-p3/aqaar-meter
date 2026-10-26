using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace AqaarMeterAPI.Models
{
    public class PredictionRequestDto
    {
        [Required]
        [JsonPropertyName("city")]
        public string City { get; set; } = string.Empty;

        [Required]
        [JsonPropertyName("district")]
        public string District { get; set; } = string.Empty;

        [Required]
        [Range(0.1, 10000.0, ErrorMessage = "Area must be between 0.1 and 10000 sqm")]
        [JsonPropertyName("area")]
        public double Area { get; set; }

        [Required]
        [Range(0, 50, ErrorMessage = "Bedrooms count must be between 0 and 50")]
        [JsonPropertyName("bedrooms")]
        public int Bedrooms { get; set; }

        [Required]
        [Range(0, 50, ErrorMessage = "Bathrooms count must be between 0 and 50")]
        [JsonPropertyName("bathrooms")]
        public int Bathrooms { get; set; }

        [Required]
        [Range(0.0, 200.0, ErrorMessage = "Property age must be between 0 and 200 years")]
        [JsonPropertyName("property_age")]
        public double PropertyAge { get; set; }

        [Required]
        [Range(0.0, 200.0, ErrorMessage = "Street width must be between 0 and 200 meters")]
        [JsonPropertyName("street_width")]
        public double StreetWidth { get; set; }

        [Required]
        [JsonPropertyName("property_type")]
        public string PropertyType { get; set; } = string.Empty;

        [Required]
        [Range(-90.0, 90.0, ErrorMessage = "Latitude must be between -90 and 90")]
        [JsonPropertyName("latitude")]
        public double Latitude { get; set; }

        [Required]
        [Range(-180.0, 180.0, ErrorMessage = "Longitude must be between -180 and 180")]
        [JsonPropertyName("longitude")]
        public double Longitude { get; set; }

        [JsonPropertyName("elevator")]
        public bool Elevator { get; set; } = false;

        [JsonPropertyName("ac")]
        public bool Ac { get; set; } = false;

        [JsonPropertyName("furnished")]
        public bool Furnished { get; set; } = false;

        [JsonPropertyName("pool")]
        public bool Pool { get; set; } = false;

        [JsonPropertyName("car_entrance")]
        public bool CarEntrance { get; set; } = false;

        [JsonPropertyName("basement")]
        public bool Basement { get; set; } = false;

        [JsonPropertyName("yard")]
        public bool Yard { get; set; } = false;

        [JsonPropertyName("livings")]
        public int Livings { get; set; } = 1;

        [JsonPropertyName("floor_number")]
        public int FloorNumber { get; set; } = 0;

        [JsonPropertyName("ketchen")]
        public bool Ketchen { get; set; } = true;
    }

    public class PredictionResponseDto
    {
        [JsonPropertyName("id")]
        public int? Id { get; set; }

        [JsonPropertyName("predicted_price")]
        public double PredictedPrice { get; set; }

        [JsonPropertyName("min_price")]
        public double MinPrice { get; set; }

        [JsonPropertyName("max_price")]
        public double MaxPrice { get; set; }

        [JsonPropertyName("confidence_score")]
        public double ConfidenceScore { get; set; }

        [JsonPropertyName("explanation")]
        public string Explanation { get; set; } = string.Empty;

        [JsonPropertyName("used_features")]
        public Dictionary<string, object> UsedFeatures { get; set; } = new();
    }
}
