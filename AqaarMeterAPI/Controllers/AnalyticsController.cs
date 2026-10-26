using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Authorization;
using AqaarMeterAPI.Data;
using AqaarMeterAPI.Models;
using System.Security.Claims;

namespace AqaarMeterAPI.Controllers
{
    [ApiController]
    [Route("api/analytics")]
    public class AnalyticsController : ControllerBase
    {
        private readonly AppraisalsDbContext _dbContext;
        private readonly ILogger<AnalyticsController> _logger;

        public AnalyticsController(AppraisalsDbContext dbContext, ILogger<AnalyticsController> logger)
        {
            _dbContext = dbContext;
            _logger = logger;
        }

        [HttpGet("trends")]
        public async Task<IActionResult> GetTrends([FromQuery] string? district = null)
        {
            _logger.LogInformation("Calculating market trends for District: {District}", district);

            // Fetch records for district
            IQueryable<MarketTransaction> txQuery = _dbContext.MarketTransactions;
            bool isDistrictSpecific = false;

            if (!string.IsNullOrEmpty(district) && district != "all")
            {
                // check if district exists in db
                var exists = await txQuery.AnyAsync(t => t.District == district);
                if (exists)
                {
                    txQuery = txQuery.Where(t => t.District == district);
                    isDistrictSpecific = true;
                }
            }

            var transactions = await txQuery.ToListAsync();

            if (!transactions.Any())
            {
                // Fallback to all data if empty
                transactions = await _dbContext.MarketTransactions.ToListAsync();
                isDistrictSpecific = false;
            }

            // 1. Avg Price per SQM by Property Type
            var avgByPropType = transactions
                .GroupBy(t => t.PropertyType)
                .Select(g => new
                {
                    PropertyType = g.Key,
                    AveragePrice = Math.Round(g.Average(t => t.Price), 2),
                    AverageArea = Math.Round(g.Average(t => t.Area), 2),
                    AveragePricePerSqm = Math.Round(g.Average(t => t.Price / t.Area), 2),
                    Volume = g.Count()
                })
                .ToList();

            // 2. Price per SQM by Property Age (New: 0-3y, Mid: 4-10y, Old: >10y)
            var avgByAge = transactions
                .GroupBy(t => {
                    if (t.Age <= 3) return "0-3 Years (حديث)";
                    if (t.Age <= 10) return "4-10 Years (متوسط)";
                    return "10+ Years (قديم)";
                })
                .Select(g => new
                {
                    AgeGroup = g.Key,
                    AveragePricePerSqm = Math.Round(g.Average(t => t.Price / t.Area), 2),
                    Volume = g.Count()
                })
                .OrderBy(x => x.AgeGroup)
                .ToList();

            // 3. Price per SQM by Street Width
            var avgByStreet = transactions
                .GroupBy(t => {
                    if (t.StreetWidth <= 10) return "Narrow (<=10m)";
                    if (t.StreetWidth <= 20) return "Medium (11-20m)";
                    return "Wide (>20m)";
                })
                .Select(g => new
                {
                    StreetWidthGroup = g.Key,
                    AveragePricePerSqm = Math.Round(g.Average(t => t.Price / t.Area), 2),
                    Volume = g.Count()
                })
                .ToList();

            return Ok(new
            {
                District = isDistrictSpecific ? district : "All Districts",
                TotalTransactions = transactions.Count,
                AveragePricePerSqm = Math.Round(transactions.Average(t => t.Price / t.Area), 2),
                ByPropertyType = avgByPropType,
                ByAge = avgByAge,
                ByStreet = avgByStreet
            });
        }

        [HttpGet("admin-stats")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> GetAdminStats()
        {
            _logger.LogInformation("Generating admin statistics...");

            var totalUsers = await _dbContext.Users.CountAsync();
            var totalValuations = await _dbContext.AppraisalLogs.CountAsync();
            var totalMarketTransactions = await _dbContext.MarketTransactions.CountAsync();

            // Find most active district in logs
            var mostActiveDistrict = "None";
            var activeDistrictGroup = await _dbContext.AppraisalLogs
                .GroupBy(l => l.District)
                .OrderByDescending(g => g.Count())
                .Select(g => new { District = g.Key, Count = g.Count() })
                .FirstOrDefaultAsync();

            if (activeDistrictGroup != null)
            {
                mostActiveDistrict = $"{activeDistrictGroup.District} ({activeDistrictGroup.Count} valuations)";
            }

            // Retrieve all users (excluding password hashes for security)
            var users = await _dbContext.Users
                .Select(u => new
                {
                    u.Id,
                    u.Username,
                    u.Email,
                    u.Role,
                    u.CreatedAt
                })
                .OrderByDescending(u => u.CreatedAt)
                .ToListAsync();

            // Recent valuations list
            var recentValuations = await _dbContext.AppraisalLogs
                .OrderByDescending(l => l.Timestamp)
                .Take(5)
                .Select(l => new
                {
                    l.Id,
                    l.Timestamp,
                    l.PropertyType,
                    l.Area,
                    l.City,
                    l.District,
                    l.PredictedPrice,
                    l.ConfidenceScore
                })
                .ToListAsync();

            return Ok(new
            {
                TotalUsers = totalUsers,
                TotalValuations = totalValuations,
                TotalMarketTransactions = totalMarketTransactions,
                MostActiveDistrict = mostActiveDistrict,
                Users = users,
                RecentValuations = recentValuations
            });
        }

        // Endpoint to allow admins to change user roles or delete users
        [HttpPut("users/{userId}/role")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> ChangeUserRole(int userId, [FromBody] ChangeRoleDto dto)
        {
            if (dto.Role != "User" && dto.Role != "Agent" && dto.Role != "Admin")
            {
                return BadRequest(new { detail = "Invalid role specified." });
            }

            var user = await _dbContext.Users.FindAsync(userId);
            if (user == null)
            {
                return NotFound(new { detail = "User not found." });
            }

            user.Role = dto.Role;
            await _dbContext.SaveChangesAsync();
            _logger.LogInformation("Admin changed role of user {Username} to {Role}", user.Username, user.Role);

            return Ok(new { detail = $"User role successfully updated to {dto.Role}." });
        }

        [HttpDelete("users/{userId}")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> DeleteUser(int userId)
        {
            var user = await _dbContext.Users.FindAsync(userId);
            if (user == null)
            {
                return NotFound(new { detail = "User not found." });
            }

            _dbContext.Users.Remove(user);
            await _dbContext.SaveChangesAsync();
            _logger.LogInformation("Admin deleted user account: {Username}", user.Username);

            return Ok(new { detail = "User account successfully deleted." });
        }
    }

    public class ChangeRoleDto
    {
        public string Role { get; set; } = string.Empty;
    }
}
