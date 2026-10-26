using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Authorization;
using AqaarMeterAPI.Data;
using AqaarMeterAPI.Models;
using System.Text;
using System.Text.Json;
using System.Security.Claims;

namespace AqaarMeterAPI.Controllers
{
    [ApiController]
    [Route("api/predict")]
    public class PredictController : ControllerBase
    {
        private readonly AppraisalsDbContext _dbContext;
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly ILogger<PredictController> _logger;
        private readonly IConfiguration _configuration;

        public PredictController(
            AppraisalsDbContext dbContext,
            IHttpClientFactory httpClientFactory,
            ILogger<PredictController> logger,
            IConfiguration configuration)
        {
            _dbContext = dbContext;
            _httpClientFactory = httpClientFactory;
            _logger = logger;
            _configuration = configuration;
        }

        [HttpPost]
        public async Task<IActionResult> Predict([FromBody] PredictionRequestDto request)
        {
            _logger.LogInformation("Received prediction request in ASP.NET Core for City: {City}, District: {District}", request.City, request.District);

            // Extract UserId from JWT if logged in (optional auth)
            int? loggedInUserId = null;
            if (User.Identity?.IsAuthenticated == true)
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier);
                if (userIdClaim != null && int.TryParse(userIdClaim.Value, out var userId))
                {
                    loggedInUserId = userId;
                }
            }

            // 1. Prepare HttpClient and send request to FastAPI microservice
            var mlServiceUrl = _configuration["MlService:BaseUrl"] ?? "http://127.0.0.1:8000";
            var client = _httpClientFactory.CreateClient();
            
            var jsonPayload = JsonSerializer.Serialize(request);
            var content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");

            PredictionResponseDto? predictionResponse = null;
            try
            {
                var response = await client.PostAsync($"{mlServiceUrl}/predict", content);
                if (!response.IsSuccessStatusCode)
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    _logger.LogError("FastAPI returned error code {StatusCode}: {Error}", response.StatusCode, errorContent);
                    return StatusCode((int)response.StatusCode, new { detail = $"ML Microservice Error: {errorContent}" });
                }

                var responseBody = await response.Content.ReadAsStringAsync();
                predictionResponse = JsonSerializer.Deserialize<PredictionResponseDto>(responseBody, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });
            }
            catch (HttpRequestException ex)
            {
                _logger.LogError(ex, "Failed to connect to FastAPI microservice at {Url}", mlServiceUrl);
                return StatusCode(503, new { detail = "Machine Learning microservice is currently unavailable. Please make sure the FastAPI server is running on port 8000." });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error calling FastAPI microservice");
                return StatusCode(500, new { detail = "Unexpected error when calling the ML backend." });
            }

            if (predictionResponse == null)
            {
                _logger.LogError("FastAPI response was empty or failed to deserialize.");
                return StatusCode(500, new { detail = "Failed to parse prediction results." });
            }

            // 2. Save prediction history to SQLite Database
            try
            {
                var log = new AppraisalLog
                {
                    Timestamp = DateTime.UtcNow,
                    UserId = loggedInUserId, // Associate with logged in user if present
                    City = request.City,
                    District = request.District,
                    Area = request.Area,
                    Bedrooms = request.Bedrooms,
                    Bathrooms = request.Bathrooms,
                    PropertyAge = request.PropertyAge,
                    StreetWidth = request.StreetWidth,
                    PropertyType = request.PropertyType,
                    Latitude = request.Latitude,
                    Longitude = request.Longitude,
                    Elevator = request.Elevator,
                    Ac = request.Ac,
                    Furnished = request.Furnished,
                    Pool = request.Pool,
                    CarEntrance = request.CarEntrance,
                    Basement = request.Basement,
                    Yard = request.Yard,
                    Livings = request.Livings,
                    FloorNumber = request.FloorNumber,
                    Ketchen = request.Ketchen,

                    PredictedPrice = predictionResponse.PredictedPrice,
                    MinPrice = predictionResponse.MinPrice,
                    MaxPrice = predictionResponse.MaxPrice,
                    ConfidenceScore = predictionResponse.ConfidenceScore,
                    Explanation = predictionResponse.Explanation
                };

                _dbContext.AppraisalLogs.Add(log);
                await _dbContext.SaveChangesAsync();
                _logger.LogInformation("Successfully saved appraisal log (ID: {Id}) associated with User: {UserId} to database.", log.Id, log.UserId);
                
                predictionResponse.Id = log.Id;
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Appraisal calculated successfully but failed to save log to SQLite database.");
            }

            // 3. Return prediction to client
            return Ok(predictionResponse);
        }

        [HttpGet("history")]
        public async Task<IActionResult> GetHistory([FromQuery] int limit = 10)
        {
            if (limit <= 0 || limit > 100)
            {
                limit = 10;
            }

            // If user is authenticated, show their personal history.
            // If they are an Admin, show all history.
            // If anonymous, return empty history or 401. Let's make it require login to view history, but admins see everything.
            if (User.Identity?.IsAuthenticated != true)
            {
                return Unauthorized(new { detail = "You must be logged in to view appraisal history." });
            }

            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier);
            var roleClaim = User.FindFirst(ClaimTypes.Role);

            if (userIdClaim == null || !int.TryParse(userIdClaim.Value, out var userId))
            {
                return Unauthorized(new { detail = "Invalid user identity claims." });
            }

            IQueryable<AppraisalLog> query = _dbContext.AppraisalLogs;

            // If NOT admin, filter by user ID
            if (roleClaim?.Value != "Admin")
            {
                query = query.Where(a => a.UserId == userId);
            }

            var logs = await query
                .OrderByDescending(a => a.Timestamp)
                .Take(limit)
                .ToListAsync();

            return Ok(logs);
        }

        [HttpGet("nearby")]
        public async Task<IActionResult> GetNearbyTransactions(
            [FromQuery] double lat,
            [FromQuery] double lng,
            [FromQuery] double radiusKm = 5.0,
            [FromQuery] string? propertyType = null,
            [FromQuery] int limit = 10)
        {
            if (radiusKm <= 0 || radiusKm > 50) radiusKm = 5.0;
            if (limit <= 0 || limit > 100) limit = 10;

            // 1. Calculate bounding box for SQLite query optimization
            // 1 degree latitude = ~111 km
            double latDelta = radiusKm / 111.0;
            double minLat = lat - latDelta;
            double maxLat = lat + latDelta;

            // 1 degree longitude = 111 * cos(latitude) km
            double radLat = Math.PI * lat / 180.0;
            double lngDelta = radiusKm / (111.0 * Math.Cos(radLat));
            double minLng = lng - lngDelta;
            double maxLng = lng + lngDelta;

            // 2. Query candidates from DB inside bounding box
            var query = _dbContext.MarketTransactions
                .Where(t => t.Latitude >= minLat && t.Latitude <= maxLat &&
                            t.Longitude >= minLng && t.Longitude <= maxLng);

            // Filter by propertyType if specified (and not 'Land' / 'sale' generic)
            if (!string.IsNullOrEmpty(propertyType) && propertyType != "all")
            {
                query = query.Where(t => t.PropertyType == propertyType);
            }

            var candidates = await query.ToListAsync();

            // 3. Filter candidates by exact Haversine distance and sort
            var nearby = candidates
                .Select(t => new
                {
                    Transaction = t,
                    DistanceKm = CalculateHaversineDistance(lat, lng, t.Latitude, t.Longitude)
                })
                .Where(x => x.DistanceKm <= radiusKm)
                .OrderBy(x => x.DistanceKm)
                .Take(limit)
                .Select(x => new
                {
                    x.Transaction.Id,
                    x.Transaction.Price,
                    x.Transaction.Area,
                    x.Transaction.Beds,
                    x.Transaction.Livings,
                    x.Transaction.Wc,
                    x.Transaction.Age,
                    x.Transaction.StreetWidth,
                    x.Transaction.Latitude,
                    x.Transaction.Longitude,
                    x.Transaction.District,
                    x.Transaction.PropertyType,
                    distance_km = Math.Round(x.DistanceKm, 2),
                    price_per_sqm = Math.Round(x.Transaction.Price / x.Transaction.Area, 2)
                })
                .ToList();

            return Ok(nearby);
        }

        private double CalculateHaversineDistance(double lat1, double lon1, double lat2, double lon2)
        {
            double r = 6371.0; // earth radius in km
            double dLat = ToRadians(lat2 - lat1);
            double dLon = ToRadians(lon2 - lon1);
            double a = Math.Sin(dLat / 2) * Math.Sin(dLat / 2) +
                       Math.Cos(ToRadians(lat1)) * Math.Cos(ToRadians(lat2)) *
                       Math.Sin(dLon / 2) * Math.Sin(dLon / 2);
            double c = 2 * Math.Asin(Math.Sqrt(a));
            return r * c;
        }

        private double ToRadians(double val)
        {
            return (Math.PI / 180) * val;
        }
    }
}
