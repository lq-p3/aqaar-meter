using System;

namespace AqaarMeterAPI.Models
{
    public class AppraisalLog
    {
        public int Id { get; set; }
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
        public int? UserId { get; set; }

        // Inputs
        public string City { get; set; } = string.Empty;
        public string District { get; set; } = string.Empty;
        public double Area { get; set; }
        public int Bedrooms { get; set; }
        public int Bathrooms { get; set; }
        public double PropertyAge { get; set; }
        public double StreetWidth { get; set; }
        public string PropertyType { get; set; } = string.Empty;
        public double Latitude { get; set; }
        public double Longitude { get; set; }
        public bool Elevator { get; set; }
        public bool Ac { get; set; }
        public bool Furnished { get; set; }
        public bool Pool { get; set; }
        public bool CarEntrance { get; set; }
        public bool Basement { get; set; }
        public bool Yard { get; set; }
        public int Livings { get; set; }
        public int FloorNumber { get; set; }
        public bool Ketchen { get; set; }

        // Outputs
        public double PredictedPrice { get; set; }
        public double MinPrice { get; set; }
        public double MaxPrice { get; set; }
        public double ConfidenceScore { get; set; }
        public string Explanation { get; set; } = string.Empty;
    }
}
