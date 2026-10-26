using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using System.Text;
using AqaarMeterAPI.Data;
using AqaarMeterAPI.Services;

var builder = WebApplication.CreateBuilder(args);

// 1. Add services to the container.
builder.Services.AddControllers();

// Configure Swagger/OpenAPI
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Configure SQLite Database
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection") ?? "Data Source=appraisals.db";
builder.Services.AddDbContext<AppraisalsDbContext>(options =>
    options.UseSqlite(connectionString));

// Register JwtService
builder.Services.AddSingleton<JwtService>();

// Configure JWT Authentication
var secretKey = builder.Configuration["Jwt:Secret"] ?? "CHANGE_ME_set_Jwt__Secret_in_environment_min_32_chars";
var issuer = builder.Configuration["Jwt:Issuer"] ?? "AqaarMeterAPI";
var audience = builder.Configuration["Jwt:Audience"] ?? "AqaarMeterFrontend";

builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true,
        ValidateAudience = true,
        ValidateLifetime = true,
        ValidateIssuerSigningKey = true,
        ValidIssuer = issuer,
        ValidAudience = audience,
        IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey))
    };
});

// Configure HttpClient Factory
builder.Services.AddHttpClient();

// Configure CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var app = builder.Build();

// 2. Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// Ensure the SQLite database is created on startup
using (var scope = app.Services.CreateScope())
{
    var services = scope.ServiceProvider;
    try
    {
        var context = services.GetRequiredService<AppraisalsDbContext>();
        context.Database.EnsureCreated();
    }
    catch (Exception ex)
    {
        var logger = services.GetRequiredService<ILogger<Program>>();
        logger.LogError(ex, "An error occurred while creating the database.");
    }
}

app.UseCors("AllowFrontend");

app.UseAuthentication(); // Enable Authentication
app.UseAuthorization();  // Enable Authorization

// Root endpoint redirect or metadata response
app.MapGet("/", () => Results.Json(new
{
    name = "AqaarMeter ASP.NET Core API Gateway",
    version = "1.0.0",
    status = "running",
    endpoints = new[] { 
        "/api/auth/register (POST)", 
        "/api/auth/login (POST)", 
        "/api/predict (POST)", 
        "/api/predict/history (GET)",
        "/api/predict/nearby (GET)",
        "/api/analytics/trends (GET)",
        "/api/analytics/admin-stats (GET)"
    }
}));

app.MapControllers();

app.Run();
