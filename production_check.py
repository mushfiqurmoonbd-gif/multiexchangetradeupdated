#!/usr/bin/env python3
"""
Production Environment Checker
Validates that all required settings are configured for production trading
"""

import os
import sys
from dotenv import load_dotenv

def check_production_ready():
    """Check if environment is ready for production trading"""
    load_dotenv()
    
    print("PRODUCTION READINESS CHECK")
    print("=" * 50)
    
    # Check API keys for all supported exchanges
    exchanges = {
        'BINANCE': {'key': 'BINANCE_API_KEY', 'secret': 'BINANCE_API_SECRET', 'passphrase': None},
        'BYBIT': {'key': 'BYBIT_API_KEY', 'secret': 'BYBIT_API_SECRET', 'passphrase': None},
        'MEXC': {'key': 'MEXC_API_KEY', 'secret': 'MEXC_API_SECRET', 'passphrase': None},
        'ALPACA': {'key': 'ALPACA_API_KEY', 'secret': 'ALPACA_API_SECRET', 'passphrase': None},
        'COINBASE': {'key': 'COINBASE_API_KEY', 'secret': 'COINBASE_API_SECRET', 'passphrase': 'COINBASE_PASSPHRASE'},
        'KRAKEN': {'key': 'KRAKEN_API_KEY', 'secret': 'KRAKEN_API_SECRET', 'passphrase': None},
    }
    
    api_keys_configured = 0
    
    for exchange_name, creds in exchanges.items():
        api_key = os.getenv(creds['key'])
        api_secret = os.getenv(creds['secret'])
        passphrase = os.getenv(creds['passphrase']) if creds['passphrase'] else None
        
        # Check if required credentials are present
        if api_key and api_secret:
            if creds['passphrase'] and not passphrase:
                print(f"[WARNING] {exchange_name}: API keys found but passphrase missing (required for Coinbase)")
            else:
                print(f"[OK] {exchange_name}: API keys configured")
                api_keys_configured += 1
        else:
            print(f"[SKIP] {exchange_name}: API keys not configured (optional)")
    
    print(f"\nAPI Keys Status: {api_keys_configured}/{len(exchanges)} exchanges configured")
    
    # Production warnings
    print("\nPRODUCTION WARNINGS:")
    print("• This will place REAL orders with REAL money")
    print("• Ensure sufficient account balance")
    print("• Test strategies thoroughly before live trading")
    print("• Monitor positions closely")
    print("• Use proper risk management settings")
    
    # Final check
    if api_keys_configured > 0:
        print(f"\nPRODUCTION READY: {api_keys_configured} exchange(s) configured")
        print("Proceed with caution - Real trading enabled!")
        return True
    else:
        print("\nNOT PRODUCTION READY: No API keys configured")
        print("Configure API keys in .env file before running production")
        return False

if __name__ == "__main__":
    check_production_ready()
