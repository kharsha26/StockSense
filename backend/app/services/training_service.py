# training_service.py
import numpy as np # type: ignore
import torch # type: ignore
import logging
from .reward_service import risk_reward

logger = logging.getLogger(__name__)

MAX_ASSETS       = 10
FEATURES_PER_ASSET = 4


# ---------------------------------------
# BUILD STATE VECTOR FROM PRICE HISTORY
# ---------------------------------------
def build_state(assets_prices: dict, step: int) -> list:
    state = []
    for symbol, prices in assets_prices.items():
        if step < 1 or step >= len(prices):
            state.extend([1.0, 0.0, 0.0, 0.5])
            continue

        current = float(prices[step])
        prev    = float(prices[step - 1])

        # Price momentum
        price_ratio = current / (prev + 1e-6)
        price_ratio = float(np.clip(price_ratio, 0.5, 2.0))

        # Short return
        ret = (current - prev) / (prev + 1e-6)

        # 10-day volatility
        window = prices[max(0, step - 10): step + 1]
        vol    = float(np.std(window) / (np.mean(window) + 1e-6)) if len(window) > 1 else 0.0

        # Normalized price position in 30-day range
        window30 = prices[max(0, step - 30): step + 1]
        lo, hi   = min(window30), max(window30)
        pos      = (current - lo) / (hi - lo + 1e-6) if hi > lo else 0.5

        state.extend([price_ratio, float(ret), vol, float(pos)])

    # Pad to fixed size
    remaining = MAX_ASSETS - len(assets_prices)
    state.extend([0.0, 0.0, 0.0, 0.0] * remaining)

    # Clean NaN/Inf
    state = [v if np.isfinite(v) else 0.0 for v in state]

    return state[:MAX_ASSETS * FEATURES_PER_ASSET]


# ---------------------------------------
# TRAIN AGENT ON MULTI-ASSET PRICE DATA
# ---------------------------------------
def train_agent(agent, states: list, prices: list) -> list:
    """
    Original single-asset training interface.
    Kept for backward compatibility.
    """
    rewards = []

    if len(states) < 10:
        logger.warning("Not enough states for training")
        return rewards

    for i in range(len(states) - 1):
        state      = np.array(states[i],     dtype=np.float32)
        next_state = np.array(states[i + 1], dtype=np.float32)

        current_price = float(prices[i])
        next_price    = float(prices[i + 1])

        if current_price == 0:
            continue

        profit = (next_price - current_price) / current_price
        profit = float(np.clip(profit, -0.5, 0.5))

        window     = prices[max(0, i - 10): i + 1]
        volatility = float(np.std(window) / (np.mean(window) + 1e-6)) if len(window) > 1 else 0.0

        reward = risk_reward(profit, volatility)
        done   = (i == len(states) - 2)
        action = agent.act(state)

        agent.remember(state, action, reward, next_state, done)
        agent.replay()
        rewards.append(reward)

    return rewards


# ---------------------------------------
# FULL MULTI-ASSET DQN TRAINING PIPELINE
# ---------------------------------------
def train_dqn_multi_asset(agent, assets_prices: dict, episodes: int = 5) -> dict:
    """
    Train DQN on multiple assets simultaneously.
    assets_prices: { symbol: [price1, price2, ...] }
    """
    if not assets_prices:
        return {"error": "No asset data provided"}

    # Align all price series to same length
    min_len = min(len(p) for p in assets_prices.values())
    if min_len < 20:
        return {"error": "Not enough price history (need 20+ days)"}

    asset_list = list(assets_prices.keys())
    aligned    = {sym: assets_prices[sym][:min_len] for sym in asset_list}

    logger.info(f" Training DQN on {len(asset_list)} assets, {min_len} steps, {episodes} episodes")

    all_rewards     = []
    episode_returns = []

    for episode in range(episodes):
        episode_reward  = 0.0
        portfolio_value = 1.0
        step_rewards    = []

        for step in range(1, min_len - 1):
            # Build state and next state
            state      = build_state(aligned, step)
            next_state = build_state(aligned, step + 1)

            state_np      = np.array(state,      dtype=np.float32)
            next_state_np = np.array(next_state, dtype=np.float32)

            # Get DQN action (index of asset to overweight)
            action = agent.act(state_np)

            # Build allocation weights — overweight chosen asset
            weights = np.ones(len(asset_list)) / len(asset_list)
            if action < len(asset_list):
                weights[action] += 0.3
                weights = weights / weights.sum()

            # Compute portfolio return
            portfolio_return = 0.0
            for idx, sym in enumerate(asset_list):
                prices  = aligned[sym]
                r       = (float(prices[step + 1]) - float(prices[step])) / (float(prices[step]) + 1e-6)
                r       = float(np.clip(r, -0.5, 0.5))
                portfolio_return += weights[idx] * r

            portfolio_value *= (1 + portfolio_return)

            # Compute volatility for reward
            recent = [
                (float(aligned[sym][step]) - float(aligned[sym][step - 1])) / (float(aligned[sym][step - 1]) + 1e-6)
                for sym in asset_list
                if step > 0
            ]
            volatility = float(np.std(recent)) if len(recent) > 1 else 0.0

            reward = risk_reward(portfolio_return, volatility)
            done   = (step == min_len - 2)

            agent.remember(state_np, action, reward, next_state_np, done)
            agent.replay()

            episode_reward += reward
            step_rewards.append(reward)

        episode_returns.append(episode_reward)
        all_rewards.extend(step_rewards)

        logger.info(
            f"  Episode {episode + 1}/{episodes} — "
            f"total_reward: {episode_reward:.4f} | "
            f"portfolio: {portfolio_value:.4f} | "
            f"epsilon: {agent.epsilon:.4f}"
        )

    # Save after training
    agent.save()

    return {
        "episodes":          episodes,
        "assets":            asset_list,
        "total_steps":       len(all_rewards),
        "avg_reward":        round(float(np.mean(all_rewards)), 6) if all_rewards else 0,
        "episode_returns":   [round(r, 4) for r in episode_returns],
        "final_epsilon":     round(agent.epsilon, 4),
        "final_train_steps": agent.train_step,
    }