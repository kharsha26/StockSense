#reward_service.py

def risk_reward(profit, volatility, risk_penalty=0.5):
    """
    Risk-aware reward function
    Reward = Profit - lambda * Volatility
    """
    return profit - risk_penalty * volatility