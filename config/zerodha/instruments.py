# config/zerodha/instruments.py
"""
Zerodha Instrument Token Management
Downloads and manages instrument master data for API calls
"""
import pandas as pd
import requests
from datetime import datetime
import os
import json

class ZerodhaInstruments:
    """Manage Zerodha instrument tokens and symbol mapping"""
    
    def __init__(self, kite=None):
        self.kite = kite
        self.instruments_file = 'config/zerodha/instruments.csv'
        self.symbol_map_file = 'config/zerodha/symbol_map.json'
        self.instruments_df = None
        self.symbol_map = {}
        
        # Load existing data
        self.load_instruments()
    
    def download_instruments(self):
        """Download latest instrument master from Zerodha"""
        try:
            print("📥 Downloading Zerodha instrument master...")
            
            if not self.kite:
                print("❌ Kite connection required")
                return False
            
            # Download instruments from Zerodha
            instruments = self.kite.instruments()
            
            if instruments:
                # Convert to DataFrame
                self.instruments_df = pd.DataFrame(instruments)
                
                # Save to CSV
                os.makedirs(os.path.dirname(self.instruments_file), exist_ok=True)
                self.instruments_df.to_csv(self.instruments_file, index=False)
                
                # Create symbol mapping for NSE stocks
                self.create_symbol_mapping()
                
                print(f"✅ Downloaded {len(instruments)} instruments")
                return True
            else:
                print("❌ No instruments data received")
                return False
                
        except Exception as e:
            print(f"❌ Instrument download error: {e}")
            return False
    
    def load_instruments(self):
        """Load instruments from saved file"""
        try:
            if os.path.exists(self.instruments_file):
                self.instruments_df = pd.read_csv(self.instruments_file)
                print(f"📊 Loaded {len(self.instruments_df)} instruments from file")
                
                # Load symbol mapping
                if os.path.exists(self.symbol_map_file):
                    with open(self.symbol_map_file, 'r') as f:
                        self.symbol_map = json.load(f)
                
                return True
            else:
                print("⚠️ No instruments file found. Run download_instruments() first.")
                return False
                
        except Exception as e:
            print(f"❌ Error loading instruments: {e}")
            return False
    
    def create_symbol_mapping(self):
        """Create mapping from symbol to instrument token"""
        try:
            if self.instruments_df is None:
                return False
            
            # Filter for NSE equity stocks
            nse_stocks = self.instruments_df[
                (self.instruments_df['exchange'] == 'NSE') & 
                (self.instruments_df['instrument_type'] == 'EQ')
            ].copy()
            
            # Create mapping
            self.symbol_map = {}
            for _, row in nse_stocks.iterrows():
                symbol = row['tradingsymbol']
                self.symbol_map[symbol] = {
                    'instrument_token': row['instrument_token'],
                    'exchange_token': row['exchange_token'],
                    'name': row['name'],
                    'lot_size': row['lot_size'],
                    'tick_size': row['tick_size']
                }
            
            # Save mapping
            with open(self.symbol_map_file, 'w') as f:
                json.dump(self.symbol_map, f, indent=2)
            
            print(f"✅ Created symbol mapping for {len(self.symbol_map)} stocks")
            return True
            
        except Exception as e:
            print(f"❌ Error creating symbol mapping: {e}")
            return False
    
    def get_instrument_token(self, symbol):
        """Get instrument token for a symbol"""
        try:
            if symbol in self.symbol_map:
                return self.symbol_map[symbol]['instrument_token']
            else:
                print(f"⚠️ Symbol {symbol} not found in mapping")
                return None
        except Exception as e:
            print(f"❌ Error getting instrument token: {e}")
            return None
    
    def get_symbol_info(self, symbol):
        """Get complete symbol information"""
        return self.symbol_map.get(symbol, None)
    
    def search_symbols(self, search_term):
        """Search for symbols containing the search term"""
        try:
            if self.instruments_df is None:
                return []
            
            # Search in trading symbols and names
            mask = (
                self.instruments_df['tradingsymbol'].str.contains(search_term, case=False, na=False) |
                self.instruments_df['name'].str.contains(search_term, case=False, na=False)
            )
            
            results = self.instruments_df[mask & (self.instruments_df['exchange'] == 'NSE')].copy()
            
            return results[['tradingsymbol', 'name', 'instrument_token']].head(10).to_dict('records')
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def update_if_needed(self):
        """Update instruments if file is older than 1 day"""
        try:
            if not os.path.exists(self.instruments_file):
                return self.download_instruments()
            
            # Check file age
            file_time = datetime.fromtimestamp(os.path.getmtime(self.instruments_file))
            if (datetime.now() - file_time).days >= 1:
                print("📅 Instruments file is old, updating...")
                return self.download_instruments()
            
            return True
            
        except Exception as e:
            print(f"❌ Update check error: {e}")
            return False

# Usage example
def setup_instruments(kite_instance):
    """Setup instruments for a Kite instance"""
    instruments = ZerodhaInstruments(kite_instance)
    
    # Update if needed
    instruments.update_if_needed()
    
    return instruments