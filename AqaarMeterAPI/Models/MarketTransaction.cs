namespace AqaarMeterAPI.Models
{
    public class MarketTransaction
    {
        public int Id { get; set; }
        public double Price { get; set; }
        public double Area { get; set; }
        public int Beds { get; set; }
        public int Livings { get; set; }
        public int Wc { get; set; }
        public double Age { get; set; }
        public double StreetWidth { get; set; }
        public double Latitude { get; set; }
        public double Longitude { get; set; }
        public string District { get; set; } = string.Empty;
        public string PropertyType { get; set; } = string.Empty; // Villa, Apartment, Duplex, Land
    }
}
