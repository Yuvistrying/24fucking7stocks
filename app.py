import os
import json
import time
import re
import requests
import pytz
from bs4 import BeautifulSoup
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from apscheduler.schedulers.background import BackgroundScheduler
from concurrent.futures import ThreadPoolExecutor, as_completed

# SQLAlchemy compatibility fix for serverless environments
import sqlalchemy
sqlalchemy.__version__ = '1.4.46'
if not hasattr(sqlalchemy, '__all__'):
    sqlalchemy.__all__ = []

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Configure database
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///stock_dashboard.db')
# Fix for Heroku PostgreSQL URLs
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
# Use pg8000 as the PostgreSQL driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)

# Database models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    tickers = db.relationship('Ticker', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def get_id(self):
        return str(self.id)

class Ticker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('symbol', 'user_id', name='unique_user_ticker'),)

# Global stock data - will be cached, but not stored in the database
STOCK_DATA = {}

# Create a lock for thread-safe access to STOCK_DATA
import threading
data_lock = threading.Lock()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def scrape_stock_data(ticker):
    """Scrape stock data from Robinhood for a given ticker"""
    url = f"https://robinhood.com/us/en/stocks/{ticker}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://robinhood.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }
    
    try:
        print(f"Scraping data for {ticker}...")
        
        # Try a more direct API approach first
        api_url = f"https://api.robinhood.com/instruments/?symbol={ticker}"
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            instrument_data = response.json()
            if instrument_data.get('results') and len(instrument_data['results']) > 0:
                instrument_id = instrument_data['results'][0]['id']
                
                # Get quote data
                quote_url = f"https://api.robinhood.com/marketdata/quotes/{instrument_id}/"
                quote_response = requests.get(quote_url, headers=headers, timeout=10)
                
                if quote_response.status_code == 200:
                    quote_data = quote_response.json()
                    
                    # Extract price and change
                    price = quote_data.get('last_trade_price', 'N/A')
                    if price != 'N/A':
                        price = f"${float(price):.2f}"
                    
                    previous_close = quote_data.get('previous_close', 'N/A')
                    if previous_close != 'N/A' and price != 'N/A':
                        previous_close = float(previous_close)
                        current_price = float(price.replace('$', ''))
                        change_amount = current_price - previous_close
                        change_percent = (change_amount / previous_close) * 100
                        change = f"{'+' if change_amount >= 0 else ''}{change_amount:.2f} ({'+' if change_amount >= 0 else ''}{change_percent:.2f}%)"
                    else:
                        change = "N/A"
                    
                    # Check if market is open
                    market_status = "Market Open" if quote_data.get('trading_halted') is False else "Market Closed"
                    
                    return {
                        'ticker': ticker,
                        'price': price,
                        'change': change,
                        'market_status': market_status,
                        'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
        
        # Fallback to the website scraping approach
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            # Try to extract data from the HTML using regex
            html_content = response.text
            
            # Save HTML for debugging
            with open(f"{ticker}_debug.html", "w") as f:
                f.write(html_content)
            
            # Look for price data in JSON embedded in the page
            json_matches = re.findall(r'{"symbol":"' + ticker + r'".+?"last_trade_price":"([^"]+)"', html_content)
            if json_matches:
                price = f"${float(json_matches[0]):.2f}"
                
                # Try to find change information
                change_matches = re.findall(r'"previous_close":"([^"]+)"', html_content)
                if change_matches:
                    previous_close = float(change_matches[0])
                    current_price = float(json_matches[0])
                    change_amount = current_price - previous_close
                    change_percent = (change_amount / previous_close) * 100
                    change = f"{'+' if change_amount >= 0 else ''}{change_amount:.2f} ({'+' if change_amount >= 0 else ''}{change_percent:.2f}%)"
                else:
                    change = "N/A"
                
                # Try to find market status
                if "Market Open" in html_content:
                    market_status = "Market Open"
                elif "After Hours" in html_content:
                    market_status = "After Hours"
                elif "Pre-market" in html_content:
                    market_status = "Pre-market"
                else:
                    market_status = "Market Closed"
                
                return {
                    'ticker': ticker,
                    'price': price,
                    'change': change,
                    'market_status': market_status,
                    'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
            # As a last resort, try to scrape the values from fixed positions in the markup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract any text that might contain a price ($ followed by numbers)
            all_text = soup.get_text()
            price_pattern = r'\$\d+\.\d+'
            price_matches = re.findall(price_pattern, all_text)
            
            if price_matches:
                price = price_matches[0]
                # Try to find text near the price that might be change information
                change = "N/A"
                market_status = "Unknown"
                
                return {
                    'ticker': ticker,
                    'price': price,
                    'change': change,
                    'market_status': market_status,
                    'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        
        # If all methods fail, use Yahoo Finance as a fallback
        yahoo_url = f"https://finance.yahoo.com/quote/{ticker}"
        yahoo_response = requests.get(yahoo_url, headers=headers, timeout=15)
        
        if yahoo_response.status_code == 200:
            soup = BeautifulSoup(yahoo_response.text, 'html.parser')
            price_element = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
            change_element = soup.find('fin-streamer', {'data-field': 'regularMarketChange'})
            change_percent_element = soup.find('fin-streamer', {'data-field': 'regularMarketChangePercent'})
            
            if price_element and change_element and change_percent_element:
                price = f"${price_element.text}"
                change = f"{change_element.text} ({change_percent_element.text})"
                market_status = "Market data from Yahoo Finance"
                
                return {
                    'ticker': ticker,
                    'price': price,
                    'change': change,
                    'market_status': market_status,
                    'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        
        # If everything failed, return error status
        return {
            'ticker': ticker,
            'price': 'Error',
            'change': 'N/A',
            'market_status': 'Error: Could not retrieve data',
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        print(f"Error scraping {ticker}: {str(e)}")
        return {
            'ticker': ticker,
            'price': 'Error',
            'change': 'Error',
            'market_status': f'Error: {str(e)}',
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def update_all_stock_data():
    """Update data for all tickers using parallel processing"""
    global STOCK_DATA
    
    print(f"Scheduler triggered update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    new_data = {}
    
    # Get all unique tickers across all users
    all_tickers = set()
    
    # Use application context when accessing the database
    with app.app_context():
        for user in User.query.all():
            for ticker in user.tickers:
                all_tickers.add(ticker.symbol)
    
    # Use ThreadPoolExecutor to scrape data in parallel
    with ThreadPoolExecutor(max_workers=7) as executor:
        # Submit all jobs
        future_to_ticker = {executor.submit(scrape_stock_data, ticker): ticker for ticker in all_tickers}
        
        # Process results as they complete
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                data = future.result()
                new_data[ticker] = data
            except Exception as exc:
                print(f"Error processing {ticker}: {exc}")
                # Provide fallback data in case of error
                new_data[ticker] = {
                    'ticker': ticker,
                    'price': 'Error',
                    'change': 'Error',
                    'market_status': f'Error: Failed to retrieve data',
                    'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
    
    # Thread-safe update of the shared data
    with data_lock:
        STOCK_DATA = new_data
    
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"Updated all stock data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (took {elapsed:.2f} seconds)")
    return new_data

# Initialize scheduler - configure to avoid shutdown issues
scheduler = BackgroundScheduler(
    timezone=pytz.UTC, 
    daemon=True,  # Changed to True so it shuts down with the main process
    job_defaults={'misfire_grace_time': 300}  # More lenient misfire grace time
)
scheduler.add_job(update_all_stock_data, 'interval', minutes=1, id='stock_updater')

# Initialize the database and create a default admin user
def initialize_database():
    """Initialize database tables and create default admin user if needed"""
    print("Initializing database...")
    # Create all tables
    db.create_all()
    
    # Check if any users exist
    if User.query.count() == 0:
        # Create default admin user
        default_admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin')
        admin_user = User(
            username='admin',
            password_hash=bcrypt.generate_password_hash(default_admin_password).decode('utf-8')
        )
        db.session.add(admin_user)
        db.session.commit()
        
        # Add default tickers for admin
        default_tickers = ['AAPL', 'MSFT', 'GOOGL']
        for symbol in default_tickers:
            ticker = Ticker(symbol=symbol, user_id=admin_user.id)
            db.session.add(ticker)
        
        db.session.commit()
        print("Created default admin user with initial tickers")
    else:
        print("Database already initialized with users")

# Initialize the scheduler in a safer way
def start_scheduler():
    try:
        if not scheduler.running:
            scheduler.start()
            print(f"Background scheduler started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Next update scheduled for {scheduler.get_job('stock_updater').next_run_time}")
    except Exception as e:
        print(f"Error starting scheduler: {str(e)}")

# Run the database initialization first
with app.app_context():
    initialize_database()

# Start the scheduler
start_scheduler()

# Initial data load - only do this with app context after db is initialized
with app.app_context():
    update_all_stock_data()

# Routes for authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if not username or not password:
            flash('Username and password are required')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('register.html')
        
        # Check if username is already taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken')
            return render_template('register.html')
        
        # Create new user
        new_user = User(username=username, password_hash=bcrypt.generate_password_hash(password).decode('utf-8'))
        db.session.add(new_user)
        db.session.commit()
        
        # Log in the new user
        login_user(new_user)
        
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Main routes
@app.route('/')
@login_required
def index():
    """Render the dashboard"""
    # Get the 'refresh' query parameter (default to False)
    refresh = request.args.get('refresh', '0') == '1'
    
    # Force a data refresh if requested via query parameter
    if refresh:
        update_all_stock_data()
    
    # Get current user's tickers
    user = current_user
    user_tickers = [ticker.symbol for ticker in user.tickers]
    
    # Filter stock data for current user's tickers
    user_stock_data = {ticker: STOCK_DATA.get(ticker, {}) for ticker in user_tickers}
    
    return render_template('index.html', stocks=user_stock_data, username=current_user.username)

# API routes
@app.route('/api/stocks')
@login_required
def api_stocks():
    """Return stock data as JSON"""
    user = current_user
    user_tickers = [ticker.symbol for ticker in user.tickers]
    user_stock_data = {ticker: STOCK_DATA.get(ticker, {}) for ticker in user_tickers}
    return jsonify(user_stock_data)

@app.route('/api/tickers')
@login_required
def api_tickers():
    """Return the list of tickers"""
    user = current_user
    user_tickers = [ticker.symbol for ticker in user.tickers]
    return jsonify({'tickers': user_tickers})

@app.route('/api/add_ticker', methods=['POST'])
@login_required
def api_add_ticker():
    """Add a new ticker to the list"""
    user = current_user
    
    ticker = request.form.get('ticker', '').strip().upper()
    
    if not ticker:
        return jsonify({'status': 'error', 'message': 'No ticker provided'}), 400
    
    # Check if ticker already exists for this user
    existing_ticker = Ticker.query.filter_by(symbol=ticker, user_id=user.id).first()
    if existing_ticker:
        return jsonify({'status': 'error', 'message': f'Ticker {ticker} is already in your list'}), 400
    
    # First check if we can get valid data for this ticker
    data = scrape_stock_data(ticker)
    
    # Check if the data indicates an error
    if 'Error' in data.get('price', '') or 'Error' in data.get('market_status', ''):
        return jsonify({
            'status': 'error', 
            'message': f'Unable to get data for ticker {ticker}. Please verify it exists and try again.',
            'data': data
        }), 400
    
    # If valid, add the new ticker
    new_ticker = Ticker(symbol=ticker, user_id=user.id)
    db.session.add(new_ticker)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': f'Added ticker {ticker}', 'data': data})

@app.route('/api/remove_ticker', methods=['POST'])
@login_required
def api_remove_ticker():
    """Remove a ticker from the list"""
    user = current_user
    
    ticker = request.form.get('ticker', '').strip().upper()
    
    if not ticker:
        return jsonify({'status': 'error', 'message': 'No ticker provided'}), 400
    
    # Check if ticker exists for this user
    existing_ticker = Ticker.query.filter_by(symbol=ticker, user_id=user.id).first()
    if not existing_ticker:
        return jsonify({'status': 'error', 'message': f'Ticker {ticker} is not in your list'}), 404
    
    # Remove the ticker
    db.session.delete(existing_ticker)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': f'Removed ticker {ticker}'})

@app.route('/api/update')
@login_required
def api_update():
    """Manually trigger an update"""
    update_all_stock_data()
    return jsonify({"status": "success", "message": "Stock data updated"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) # Force redeploy comment
