from alpaca.data.historical import StockHistoricalDataClient

from agents.strategy_metrics import StrategyMetrics
from strategies.scoring_strategy import generate_strategy_signal


class StrategyAgent:
    """
    Strategy agent for a simple price-vs-SMA rule.

    This is intentionally small so you can later swap the decision logic with
    AI prompts, model predictions, or a more advanced technical strategy.
    """

    def __init__(
        self,
        min_risk_reward: float = 1.5,
        min_volume_for_signal: float = 0.75,
        min_score_gap: int = 2,
        avoid_range_trades: bool = True,
    ):
        self.min_risk_reward = min_risk_reward
        self.min_volume_for_signal = min_volume_for_signal
        self.min_score_gap = min_score_gap
        self.avoid_range_trades = avoid_range_trades

    def evaluate(
        self,
        market_data_client: StockHistoricalDataClient,
        symbol: str,
        sma_period: int,
        data_feed,
        history_start,
    ) -> dict:
        metrics = StrategyMetrics().collect(
            market_data_client=market_data_client,
            symbol=symbol,
            sma_period=sma_period,
            data_feed=data_feed,
            history_start=history_start,
        )

        signal_result = generate_strategy_signal(
            metrics,
            min_volume_for_signal=self.min_volume_for_signal,
            min_score_gap=self.min_score_gap,
            avoid_range_trades=self.avoid_range_trades,
        )
        decision = self._choose_decision(signal_result)
        reason = self._build_decision_reason(
            signal_result=signal_result,
            decision=decision,
        )

        return metrics | {
            "decision": decision,
            "strategy_signal": signal_result["signal"],
            "reason": reason,
            "buy_score": signal_result["buy_score"],
            "sell_score": signal_result["sell_score"],
            "confidence": signal_result["confidence"],
            "stop_loss": signal_result["stop_loss"],
            "take_profit": signal_result["take_profit"],
            "risk_reward_ratio": signal_result["risk_reward_ratio"],
        }

    def _build_decision_reason(self, signal_result: dict, decision: str) -> str:
        explanation = signal_result["explanation"]

        if signal_result["signal"] != "HOLD" and decision == "hold":
            return (
                f"{explanation} Trade held because risk/reward is below "
                f"the required {self.min_risk_reward:.2f}:1."
            )

        return explanation

    # Key decision logic.
    def _choose_decision(self, signal_result: dict) -> str:
        """
        Define the strategy decision rule from indicator scores.

        The scoring logic lives in strategies/scoring_strategy.py. This method converts that
        beginner-friendly BUY/SELL/HOLD signal into the lowercase decision
        format used by the rest of the trading workflow.
        """
        if signal_result["signal"] == "HOLD":
            return "hold"

        risk_reward_ratio = signal_result["risk_reward_ratio"]
        if risk_reward_ratio is None or risk_reward_ratio < self.min_risk_reward:
            return "hold"

        if signal_result["buy_score"] > signal_result["sell_score"]:
            return "buy"

        if signal_result["sell_score"] > signal_result["buy_score"]:
            return "sell"

        return "hold"
