import pandas as pd
import numpy as np

def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    """
    Calculate Stochastic Oscillator (%K line)
    
    Args:
        high: High prices series
        low: Low prices series
        close: Close prices series
        length: Period for calculation (default: 14)
    
    Returns:
        Stochastic %K values as Series
    """
    lowest_low = low.rolling(window=length, min_periods=1).min()
    highest_high = high.rolling(window=length, min_periods=1).max()
    
    stoch_k = 100 * ((close - lowest_low) / (highest_high - lowest_low + 1e-10))
    
    return stoch_k

