# GitHub Actions Setup

## Add Secrets to GitHub Repository

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these 3 secrets:

| Secret Name | Value |
|-------------|-------|
| `SUPABASE_URL` | `https://hssnbnsffqorupviykha.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Your service role key from .env |
| `OPENWEATHERMAP_API_KEY` | Your OpenWeatherMap key from .env |

## Schedule

| Collector | Schedule | Cron |
|-----------|----------|------|
| Weather | Every 12h | `0 0,12 * * *` |
| News | Every 6h | `0 0,6,12,18 * * *` |
| Vessels | Every 4h | `0 */4 * * *` |

## Manual Trigger

Go to **Actions** → **Data Collection** → **Run workflow** to trigger manually.

## Free Tier Limits

- GitHub: 2000 min/month free
- Each run: ~1-2 min
- Daily usage: ~12 min
- Monthly: ~360 min (18% of free tier)
