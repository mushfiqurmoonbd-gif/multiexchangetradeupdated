import pandas as pd
import numpy as np

def parabolic_sar(high: pd.Series, low: pd.Series, close: pd.Series, 
                  af_start: float = 0.02, af_increment: float = 0.02, 
                  af_max: float = 0.2) -> pd.Series:
    """
    Calculate Parabolic SAR (Stop and Reverse)
    
    Args:
        high: High prices series
        low: Low prices series
        close: Close prices series
        af_start: Acceleration factor start (default: 0.02)
        af_increment: Acceleration factor increment (default: 0.02)
        af_max: Acceleration factor maximum (default: 0.2)
    
    Returns:
        Parabolic SAR values as Series
    """
    sar = pd.Series(index=high.index, dtype=float)
    trend = pd.Series(index=high.index, dtype=int)  # 1 for uptrend, -1 for downtrend
    ep = pd.Series(index=high.index, dtype=float)  # Extreme point
    af = pd.Series(index=high.index, dtype=float)  # Acceleration factor
    
    # Initialize first values
    sar.iloc[0] = low.iloc[0]
    trend.iloc[0] = 1  # Start in uptrend
    ep.iloc[0] = high.iloc[0]
    af.iloc[0] = af_start
    
    # Calculate SAR for each bar
    for i in range(1, len(high)):
        prev_sar = sar.iloc[i-1]
        prev_trend = trend.iloc[i-1]
        prev_ep = ep.iloc[i-1]
        prev_af = af.iloc[i-1]
        
        # Calculate SAR for current bar based on previous trend
        if prev_trend == 1:
            # Uptrend SAR calculation
            current_sar = prev_sar + prev_af * (prev_ep - prev_sar)
            # SAR cannot be above low of previous bar
            current_sar = min(current_sar, low.iloc[i-1])
            
            # Check for trend reversal
            if close.iloc[i] < current_sar:
                # Trend reverses to downtrend
                current_sar = prev_ep
                trend.iloc[i] = -1
                ep.iloc[i] = low.iloc[i]
                af.iloc[i] = af_start
            else:
                # Continue uptrend
                trend.iloc[i] = 1
                # Update extreme point
                if high.iloc[i] > prev_ep:
                    ep.iloc[i] = high.iloc[i]
                    # Increase acceleration factor
                    new_af = prev_af + af_increment
                    af.iloc[i] = min(new_af, af_max)
                else:
                    ep.iloc[i] = prev_ep
                    af.iloc[i] = prev_af
        else:
            # Downtrend SAR calculation
            current_sar = prev_sar + prev_af * (prev_ep - prev_sar)
            # SAR cannot be below high of previous bar
            current_sar = max(current_sar, high.iloc[i-1])
            
            # Check for trend reversal
            if close.iloc[i] > current_sar:
                # Trend reverses to uptrend
                current_sar = prev_ep
                trend.iloc[i] = 1
                ep.iloc[i] = high.iloc[i]
                af.iloc[i] = af_start
            else:
                # Continue downtrend
                trend.iloc[i] = -1
                # Update extreme point
                if low.iloc[i] < prev_ep:
                    ep.iloc[i] = low.iloc[i]
                    # Increase acceleration factor
                    new_af = prev_af + af_increment
                    af.iloc[i] = min(new_af, af_max)
                else:
                    ep.iloc[i] = prev_ep
                    af.iloc[i] = prev_af
        
        sar.iloc[i] = current_sar
    
    return sar

