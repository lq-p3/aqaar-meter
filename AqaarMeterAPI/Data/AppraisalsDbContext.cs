using Microsoft.EntityFrameworkCore;
using AqaarMeterAPI.Models;

namespace AqaarMeterAPI.Data
{
    public class AppraisalsDbContext : DbContext
    {
        public AppraisalsDbContext(DbContextOptions<AppraisalsDbContext> options)
            : base(options)
        {
        }

        public DbSet<AppraisalLog> AppraisalLogs { get; set; }
        public DbSet<User> Users { get; set; }
        public DbSet<MarketTransaction> MarketTransactions { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);
            
            // 1. AppraisalLog Configurations
            modelBuilder.Entity<AppraisalLog>()
                .HasIndex(a => a.Timestamp);

            modelBuilder.Entity<AppraisalLog>()
                .HasIndex(a => new { a.City, a.District });

            modelBuilder.Entity<AppraisalLog>()
                .HasIndex(a => a.UserId);

            // 2. User Configurations
            modelBuilder.Entity<User>()
                .HasIndex(u => u.Username)
                .IsUnique();

            modelBuilder.Entity<User>()
                .HasIndex(u => u.Email)
                .IsUnique();

            // 3. MarketTransaction Configurations
            modelBuilder.Entity<MarketTransaction>()
                .HasIndex(m => new { m.Latitude, m.Longitude });

            modelBuilder.Entity<MarketTransaction>()
                .HasIndex(m => m.District);
        }
    }
}
