# 24/7 Stock Dashboard

A real-time stock dashboard that displays stock prices, changes, and market status. Features user authentication so each user can manage their own list of stock tickers.

## Features

- **User Authentication**: Sign in and register using Firebase Authentication
- **Personal Ticker Lists**: Each user has their own customizable list of stocks
- **Real-time Updates**: Stock data refreshes automatically every minute
- **Realtime Database**: Firebase Realtime Database for instant data synchronization
- **Stable UI**: Components maintain their positions during updates
- **Persistent Layout**: Remembers the arrangement of your stocks between sessions
- **Mobile-Friendly Design**: Responsive interface works on all devices
- **Drag and Drop**: Reorder your stock cards with intuitive drag and drop
- **Cloud Functions**: Backend processing with Firebase Cloud Functions

## Deployment Options

This application can be deployed in two ways:

### 1. Firebase Deployment (Recommended)

For complete Firebase setup and deployment instructions, see [FIREBASE_SETUP.md](FIREBASE_SETUP.md)

### 2. Vercel with PostgreSQL

For Vercel deployment instructions, see [DEPLOY.md](DEPLOY.md)

## Demo

After deployment, you can access your app at:
- Firebase: `https://your-project-id.web.app`
- Vercel: `https://your-vercel-deployment-url.vercel.app`

## Local Development

### Requirements

- Node.js 14+ (for Firebase Functions)
- Firebase CLI (`npm install -g firebase-tools`)
- Python 3.7+ (for Flask backend if using Vercel option)

### Firebase Setup

1. **Install Dependencies**
   ```
   cd functions
   npm install
   ```

2. **Start Firebase Emulators**
   ```
   firebase emulators:start
   ```

3. **Access the App**
   
   Open a browser and navigate to the URL shown in the Firebase CLI output

### Flask Setup (Alternative)

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
- Built with Firebase, Node.js, Express, JavaScript, and Bootstrap 5
