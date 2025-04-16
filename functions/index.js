const functions = require('firebase-functions');
const admin = require('firebase-admin');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const cheerio = require('cheerio');

// Initialize Firebase Admin
admin.initializeApp();
const db = admin.database();

// Initialize Express app
const app = express();
app.use(cors({ origin: true }));
app.use(express.json());

// Global stock data cache
let STOCK_DATA = {};

// Helper function to scrape stock data
async function scrapeStockData(ticker) {
  try {
    console.log(`Scraping data for ${ticker}...`);
    const url = `https://finance.yahoo.com/quote/${ticker}`;
    const response = await axios.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
      },
      timeout: 10000
    });
    
    const $ = cheerio.load(response.data);
    
    // Extract price data
    const price = $('[data-test="qsp-price"]').text().trim();
    const change = $('[data-test="qsp-price-change"]').text().trim();
    
    // Check if we got valid data
    if (!price) {
      throw new Error(`Failed to extract price for ${ticker}`);
    }
    
    return {
      symbol: ticker,
      price: parseFloat(price.replace(/,/g, '')),
      change: change,
      last_updated: new Date().toISOString()
    };
  } catch (error) {
    console.error(`Error scraping ${ticker}:`, error.message);
    
    // Fallback method - try to get data from an API
    try {
      console.log(`Attempting fallback for ${ticker}...`);
      const apiUrl = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}`;
      const apiResponse = await axios.get(apiUrl, { timeout: 8000 });
      const result = apiResponse.data.chart.result[0];
      
      const price = result.meta.regularMarketPrice;
      const previousClose = result.meta.previousClose;
      const change = price - previousClose;
      const changePercent = (change / previousClose) * 100;
      
      return {
        symbol: ticker,
        price: price,
        change: `${change.toFixed(2)} (${changePercent.toFixed(2)}%)`,
        last_updated: new Date().toISOString()
      };
    } catch (fallbackError) {
      console.error(`Fallback for ${ticker} also failed:`, fallbackError.message);
      // Return a placeholder with error information
      return {
        symbol: ticker,
        price: null,
        change: 'Error fetching data',
        last_updated: new Date().toISOString(),
        error: true
      };
    }
  }
}

// Update all stock data
async function updateAllStockData() {
  try {
    // Get all unique tickers from all users
    const usersSnapshot = await db.ref('users').once('value');
    const users = usersSnapshot.val() || {};
    
    // Collect all tickers from all users
    let allTickers = [];
    
    Object.values(users).forEach(user => {
      if (user.tickers && Array.isArray(user.tickers)) {
        allTickers = allTickers.concat(user.tickers);
      }
    });
    
    // Deduplicate tickers
    allTickers = [...new Set(allTickers)];
    
    // No tickers to update
    if (allTickers.length === 0) {
      console.log('No tickers to update');
      return;
    }
    
    console.log(`Updating data for ${allTickers.length} tickers...`);
    
    // Scrape data for each ticker
    const promises = allTickers.map(ticker => scrapeStockData(ticker));
    const results = await Promise.all(promises);
    
    // Update STOCK_DATA and save to Firebase
    const stockUpdates = {};
    results.forEach(data => {
      if (data && data.symbol) {
        STOCK_DATA[data.symbol] = data;
        stockUpdates[data.symbol] = data;
      }
    });
    
    // Save the updated stock data to Firebase
    await db.ref('stocks').update(stockUpdates);
    console.log('Stock data updated successfully');
  } catch (error) {
    console.error('Error updating stock data:', error);
  }
}

// Middleware to catch errors
const asyncMiddleware = fn => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

// API endpoints

// Get all stocks
app.get('/api/stocks', asyncMiddleware(async (req, res) => {
  // Get stock data from Firebase
  const stocksSnapshot = await db.ref('stocks').once('value');
  const stocks = stocksSnapshot.val() || {};
  
  res.json(stocks);
}));

// Get user's tickers
app.get('/api/tickers', asyncMiddleware(async (req, res) => {
  // Get the user ID from the authenticated request
  const userId = req.query.userId;
  if (!userId) {
    return res.status(401).json({ error: 'User ID required' });
  }
  
  // Get the user's tickers from Firebase
  const tickersSnapshot = await db.ref(`users/${userId}/tickers`).once('value');
  const tickers = tickersSnapshot.val() || [];
  
  res.json(tickers);
}));

// Add a ticker
app.post('/api/add_ticker', asyncMiddleware(async (req, res) => {
  const { ticker, userId } = req.body;
  
  if (!ticker || !userId) {
    return res.status(400).json({ error: 'Ticker symbol and user ID are required' });
  }
  
  // Validate ticker symbol
  const validTicker = ticker.toUpperCase().match(/^[A-Z0-9.]{1,10}$/);
  if (!validTicker) {
    return res.status(400).json({ error: 'Invalid ticker symbol' });
  }
  
  // Get user's current tickers
  const tickersSnapshot = await db.ref(`users/${userId}/tickers`).once('value');
  const tickers = tickersSnapshot.val() || [];
  
  // Check if ticker already exists
  if (tickers.includes(ticker)) {
    return res.status(400).json({ error: 'Ticker already exists' });
  }
  
  // Add the new ticker
  const updatedTickers = [...tickers, ticker];
  await db.ref(`users/${userId}/tickers`).set(updatedTickers);
  
  // Fetch data for the new ticker
  const stockData = await scrapeStockData(ticker);
  
  // Update the stock data in Firebase
  await db.ref(`stocks/${ticker}`).set(stockData);
  
  res.json({ success: true, ticker });
}));

// Remove a ticker
app.post('/api/remove_ticker', asyncMiddleware(async (req, res) => {
  const { ticker, userId } = req.body;
  
  if (!ticker || !userId) {
    return res.status(400).json({ error: 'Ticker symbol and user ID are required' });
  }
  
  // Get user's current tickers
  const tickersSnapshot = await db.ref(`users/${userId}/tickers`).once('value');
  const tickers = tickersSnapshot.val() || [];
  
  // Filter out the ticker to remove
  const updatedTickers = tickers.filter(t => t !== ticker);
  
  // Update the user's tickers
  await db.ref(`users/${userId}/tickers`).set(updatedTickers);
  
  res.json({ success: true, ticker });
}));

// Force update of stock data
app.get('/api/update', asyncMiddleware(async (req, res) => {
  await updateAllStockData();
  res.json({ success: true, message: 'Stock data updated' });
}));

// Authentication endpoints

// User signup
app.post('/auth/signup', asyncMiddleware(async (req, res) => {
  const { email, password, username } = req.body;
  
  if (!email || !password || !username) {
    return res.status(400).json({ error: 'Email, password, and username are required' });
  }
  
  // Create the user in Firebase Authentication
  const userRecord = await admin.auth().createUser({
    email,
    password,
    displayName: username
  });
  
  // Create the user's profile in the database
  await db.ref(`users/${userRecord.uid}`).set({
    username,
    email,
    tickers: ['AAPL', 'MSFT', 'GOOGL'], // Default tickers
    created_at: admin.database.ServerValue.TIMESTAMP
  });
  
  res.json({ success: true, uid: userRecord.uid });
}));

// Error handler
app.use((err, req, res, next) => {
  console.error('API Error:', err);
  res.status(500).json({ error: 'Server error', message: err.message });
});

// Serve the dashboard
app.get('/', (req, res) => {
  res.sendFile('index.html', { root: 'public' });
});

// Schedule the stock data update (every 1 minute)
exports.scheduledUpdate = functions.pubsub.schedule('every 1 minutes').onRun(async (context) => {
  await updateAllStockData();
  return null;
});

// Daily initialization (runs once per day to ensure data is fresh)
exports.dailyInit = functions.pubsub.schedule('every 24 hours').onRun(async (context) => {
  try {
    // Clear cached data to force fresh scraping
    STOCK_DATA = {};
    console.log("Performing daily initialization...");
    await updateAllStockData();
    console.log("Daily initialization completed.");
    return null;
  } catch (error) {
    console.error("Error during daily initialization:", error);
    return null;
  }
});

// Export the Express app as a Firebase Function
exports.app = functions.https.onRequest(app); 