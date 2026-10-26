using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Identity;
using AqaarMeterAPI.Data;
using AqaarMeterAPI.Models;
using AqaarMeterAPI.Services;

namespace AqaarMeterAPI.Controllers
{
    [ApiController]
    [Route("api/auth")]
    public class AuthController : ControllerBase
    {
        private readonly AppraisalsDbContext _dbContext;
        private readonly JwtService _jwtService;
        private readonly PasswordHasher<User> _passwordHasher;
        private readonly ILogger<AuthController> _logger;

        public AuthController(
            AppraisalsDbContext dbContext,
            JwtService jwtService,
            ILogger<AuthController> logger)
        {
            _dbContext = dbContext;
            _jwtService = jwtService;
            _passwordHasher = new PasswordHasher<User>();
            _logger = logger;
        }

        [HttpPost("register")]
        public async Task<IActionResult> Register([FromBody] RegisterDto dto)
        {
            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            // Normalise username/email
            var username = dto.Username.Trim();
            var email = dto.Email.Trim().ToLower();

            // Check if username already exists
            if (await _dbContext.Users.AnyAsync(u => u.Username.ToLower() == username.ToLower()))
            {
                return BadRequest(new { detail = "Username is already taken." });
            }

            // Check if email already exists
            if (await _dbContext.Users.AnyAsync(u => u.Email.ToLower() == email))
            {
                return BadRequest(new { detail = "Email is already registered." });
            }

            // Determine role (constrain to valid roles)
            var role = "User";
            if (dto.Role == "Agent" || dto.Role == "Admin")
            {
                role = dto.Role;
            }

            // Create new User instance
            var user = new User
            {
                Username = username,
                Email = email,
                Role = role,
                CreatedAt = DateTime.UtcNow
            };

            // Hash password
            user.PasswordHash = _passwordHasher.HashPassword(user, dto.Password);

            try
            {
                _dbContext.Users.Add(user);
                await _dbContext.SaveChangesAsync();
                _logger.LogInformation("Successfully registered new user: {Username} with role {Role}", user.Username, user.Role);

                // Auto-login on register
                var token = _jwtService.GenerateToken(user);
                return Ok(new AuthResponseDto
                {
                    Token = token,
                    Username = user.Username,
                    Email = user.Email,
                    Role = user.Role
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to register user: {Username}", username);
                return StatusCode(500, new { detail = "Internal database error occurred during registration." });
            }
        }

        [HttpPost("login")]
        public async Task<IActionResult> Login([FromBody] LoginDto dto)
        {
            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            var identifier = dto.UsernameOrEmail.Trim().ToLower();

            // Search user by username or email
            var user = await _dbContext.Users.FirstOrDefaultAsync(u =>
                u.Username.ToLower() == identifier || u.Email.ToLower() == identifier);

            if (user == null)
            {
                return Unauthorized(new { detail = "Invalid username/email or password." });
            }

            // Verify password
            var verificationResult = _passwordHasher.VerifyHashedPassword(user, user.PasswordHash, dto.Password);
            if (verificationResult == PasswordVerificationResult.Failed)
            {
                return Unauthorized(new { detail = "Invalid username/email or password." });
            }

            _logger.LogInformation("User logged in successfully: {Username}", user.Username);

            // Generate JWT Token
            var token = _jwtService.GenerateToken(user);

            return Ok(new AuthResponseDto
            {
                Token = token,
                Username = user.Username,
                Email = user.Email,
                Role = user.Role
            });
        }
    }
}
