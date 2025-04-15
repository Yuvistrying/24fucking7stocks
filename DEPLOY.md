# Deploying to Vercel with PostgreSQL

This guide walks you through deploying your Stock Dashboard on Vercel with a PostgreSQL database.

## Step 1: Set Up a PostgreSQL Database

1. Sign up for a free PostgreSQL database service such as [Supabase](https://supabase.com/) or [Neon](https://neon.tech/).

2. Create a new PostgreSQL database.

3. Once created, obtain your PostgreSQL connection string (DATABASE_URL). It should look like:
   ```
   postgresql://username:password@hostname:port/database
   ```

## Step 2: Deploy to Vercel

1. Create a [Vercel account](https://vercel.com/signup) if you don't have one.

2. Install the Vercel CLI (optional):
   ```bash
   npm install -g vercel
   ```

3. Push your code to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/stock-dashboard.git
   git push -u origin main
   ```

4. Deploy using the Vercel Dashboard:
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "Add New" → "Project"
   - Import your GitHub repository
   - Configure the project with the following environment variables:
     - `DATABASE_URL`: Your PostgreSQL connection string from Step 1
     - `SECRET_KEY`: A secure random string for your Flask app
     - `DEFAULT_ADMIN_PASSWORD`: Password for the default admin user (optional, defaults to "admin")
   - Click "Deploy"

## Step 3: Verify Your Deployment

1. Once deployed, Vercel will provide you with a URL like `https://your-project.vercel.app`

2. Visit your application and log in with:
   - Username: `admin`
   - Password: Either your custom `DEFAULT_ADMIN_PASSWORD` or `admin` if you didn't set a custom one

3. Start adding your stock tickers and enjoy your live dashboard!

## Troubleshooting

- **Database Connection Issues**: Make sure your DATABASE_URL is correct and that your database allows connections from Vercel's IP addresses.
- **API Rate Limits**: If you're getting errors with stock data, you might be hitting API rate limits. Consider implementing caching or throttling.
- **Cold Start Delays**: Serverless functions might have a "cold start" delay. The first request after inactivity might take a few seconds.

## Maintaining Your App

- **Updating Code**: Push changes to your GitHub repository, and Vercel will automatically redeploy.
- **Database Backups**: Regularly backup your PostgreSQL database using your database provider's tools.
- **Monitoring**: Use Vercel's built-in analytics to monitor your application's performance. 