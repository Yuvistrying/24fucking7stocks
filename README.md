# 24/7 Stock Dashboard

A real-time stock dashboard that displays stock prices, changes, and market status. Features user authentication so each user can manage their own list of stock tickers.

## Features

- **User Authentication**: Simple login and registration system
- **Personal Ticker Lists**: Each user has their own customizable list of stocks
- **Real-time Updates**: Stock data refreshes automatically every 5 seconds
- **Stable UI**: Components maintain their positions during updates
- **Persistent Layout**: Remembers the arrangement of your stocks between sessions
- **Mobile-Friendly Design**: Responsive interface works on all devices
- **Database Storage**: PostgreSQL database for user data and preferences

## Demo

Access the live demo at: [https://your-vercel-deployment-url.vercel.app](https://your-vercel-deployment-url.vercel.app)

**Default Admin Account:**
- Username: admin
- Password: admin

## Deployment on Vercel with PostgreSQL

For complete deployment instructions, see [DEPLOY.md](DEPLOY.md)

### Quick Start:

1. Set up a PostgreSQL database on [Supabase](https://supabase.com/) or [Neon](https://neon.tech/)
2. Push your code to GitHub
3. Connect to Vercel and set the following environment variables:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `SECRET_KEY`: A secure random string
   - `DEFAULT_ADMIN_PASSWORD`: Custom admin password (optional)

## Local Development

### Requirements

- Python 3.7+
- Flask and other dependencies listed in `requirements.txt`

### Setup

1. **Install Dependencies**
   ```
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```
   python app.py
   ```

3. **Access the App**
   
   Open a browser and navigate to `http://localhost:5001`

## License

MIT

## Acknowledgements

- Stock data scraped from public sources
- Built with Flask, Bootstrap, JavaScript, and PostgreSQL
