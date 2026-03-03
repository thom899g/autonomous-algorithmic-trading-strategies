"""
Mock Market Data Generator
Generates synthetic OHLCV data for testing and validation
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MockDataConfig:
    """Configuration for mock data generation"""
    start_date: str = "2024-01-01"
    days: int = 100
    symbols: List[str] = None
    base_price: float = 100.0
    volatility: float = 0.02
    time_frame: str = "1min"
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["BTC/USDT", "ETH/USDT", "AAPL", "MSFT"]

class MockDataGenerator:
    """Generate realistic mock market data for validation testing"""
    
    def __init__(self, config: MockDataConfig = None):
        self.config = config or MockDataConfig()
        logger.info(f"Initialized MockDataGenerator with {len(self.config.symbols)} symbols")
        
    def generate_ohlcv_dataframe(self, symbol: str) -> pd.DataFrame:
        """
        Generate OHLCV DataFrame for a symbol with realistic patterns
        
        Args:
            symbol: Trading symbol
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        logger.info(f"Generating OHLCV data for {symbol}")
        
        # Generate timestamps
        start_dt = datetime.strptime(self.config.start_date, "%Y-%m-%d")
        timestamps = []
        current = start_dt
        
        # Generate more granular data for crypto vs stocks
        if "/" in symbol:  # Crypto symbol
            intervals = 1440 * self.config.days  # 1min intervals for 100 days
            delta = timedelta(minutes=1)
        else:  # Stock symbol
            intervals = 390 * self.config.days  # 1min intervals for trading hours only
            delta = timedelta(minutes=1)
        
        for _ in range(intervals):
            # Skip weekends for stocks
            if "/" not in symbol and current.weekday() >= 5:
                current += delta
                continue
            # Skip non-market hours for stocks (9:30-16:00)
            if "/" not in symbol and not (9.5 <= current.hour + current.minute/60 <= 16):
                current += delta
                continue
                
            timestamps.append(current)
            current += delta
        
        # Generate price series with realistic volatility
        n_points = len(timestamps)
        returns = np.random.normal(0, self.config.volatility, n_points)
        
        # Add some market patterns
        trend = np.linspace(0, 0.1, n_points)  # Slight upward trend
        seasonality = 0.01 * np.sin(np.linspace(0, 10 * np.pi, n_points))
        
        price_series = self.config.base_price * np.exp(np.cumsum(returns)) * (1 + trend + seasonality)
        
        # Generate OHLCV from price series
        data = []
        for i in range(0, n_points, 5):  # 5-minute bars
            if i + 4 >= n_points:
                break
                
            chunk = price_series[i:i+5]
            open_price = chunk[0]
            high = np.max(chunk)
            low = np.min(chunk)
            close = chunk[-1]
            volume = np.random.lognormal(mean=10, sigma=1.5)
            
            data.append({
                'timestamp': timestamps[i],
                'open': round(open_price, 4),
                'high': round(high, 4),
                'low': round(low, 4),
                'close': round(close, 4),
                'volume': round(volume, 2)
            })
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} bars for {symbol}")
        return df
    
    def save_to_csv(self, df: pd.DataFrame, symbol: str, filename: str = None) -> str:
        """Save DataFrame to CSV with proper formatting"""
        if filename is None:
            filename = f"mock_data_{symbol.replace('/', '_')}.csv"
        
        df.to_csv(filename, index=False)
        logger.info(f"Saved mock data to {filename}")
        return filename
    
    def save_to_json(self, df: pd.DataFrame, symbol: str, filename: str = None) -> str:
        """Save DataFrame to JSON for API-like responses"""
        if filename is None:
            filename = f"mock_data_{symbol.replace('/', '_')}.json"
        
        # Convert to dict with proper timestamp formatting
        data_dict = {
            'symbol': symbol,
            'data': df.to_dict('records')
        }
        
        with open(filename, 'w') as f:
            json.dump(data_dict, f, default=str)
        
        logger.info(f"Saved mock data to {filename}")
        return filename
    
    def generate_all_symbols(self) -> Dict[str, pd.DataFrame]:
        """Generate mock data for all configured symbols"""
        results = {}
        
        for symbol in self.config.symbols:
            try:
                df = self.generate_ohlcv_dataframe(symbol)
                results[symbol] = df
                logger.info(f"Successfully generated data for {symbol}")
            except Exception as e:
                logger.error(f"Failed to generate data for {symbol}: {e}")
                continue
        
        return results

# Example usage
if