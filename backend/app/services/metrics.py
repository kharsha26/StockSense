import numpy as np

def calculate_sharpe_ratio(returns, risk_free_rate=0.01):
    returns = np.array(returns)

    if len(returns) < 2:
        return 0

    excess_returns = returns - risk_free_rate
    sharpe = np.mean(excess_returns) / np.std(excess_returns)

    return round(float(sharpe), 3)






