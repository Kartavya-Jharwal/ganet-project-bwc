with open("quant_monitor/main.py", encoding="utf-8") as f:
    text = f.read()

insertion = """
        # 6.5 Persist signals to Appwrite
        try:
            from quant_monitor.data.appwrite_client import create_appwrite_client
            aw = create_appwrite_client()
            for ticker, result in fused.items():
                aw.write_signal(
                    ticker=ticker,
                    technical_score=tech_scores.get(ticker, 0.0),
                    fundamental_score=fund_scores.get(ticker, 0.0),
                    sentiment_score=sent_scores.get(ticker, 0.0),
                    macro_score=macro_score,
                    fused_score=result["fused_score"],
                    confidence=result["confidence"],
                    action=result["action"],
                    regime=regime,
                    dominant_model=result.get("dominant_model"),
                )

            # Also write regime history
            from quant_monitor.features.volatility import realized_volatility, hurst_exponent
            spy_returns = prices.loc["SPY"]["close"].pct_change().dropna() if "SPY" in prices.index.get_level_values(0) else None
            if spy_returns is not None:
                aw.write_regime(
                    regime=regime,
                    vix=macro.get("vix", 0.0),
                    hurst=float(hurst_exponent(prices.loc["SPY"]["close"])),
                    vol_percentile=0.0,  # populated from vol computation above
                )

            logger.info("Signals + regime persisted to Appwrite")
        except Exception as e:
            logger.warning("Failed to persist to Appwrite: %s", e)

        # 7. Dispatch alerts for actionable signals
        import asyncio
        from quant_monitor.agent.alerts import AlertDispatcher, AlertType, AlertPriority
        dispatcher = AlertDispatcher()

        for ticker, result in fused.items():
            if result["action"] in ("BUY", "SELL"):
                msg = (
                    f"<b>{ticker}</b>: {result['action']}\\n"
                    f"Score: {result['fused_score']:.3f} | Confidence: {result['confidence']:.3f}\\n"
                    f"Dominant model: {result['dominant_model']}"
                )
                asyncio.run(dispatcher.send_alert(
                    alert_type=AlertType.REBALANCE,
                    priority=AlertPriority.HIGH,
                    message=msg,
                    ticker=ticker,
                ))

        if macro_regime == "CRISIS":
            msg = dispatcher.format_macro_shift_alert("TRANSITION", "CRISIS", macro)
            asyncio.run(dispatcher.send_alert(
                alert_type=AlertType.MACRO_SHIFT,
                priority=AlertPriority.CRITICAL,
                message=msg,
            ))
"""

text = text.replace(
    '        if executed > 0:\n            logger.info("Phase 7 Orchestrator: Output %d valid execution targets.", executed)',
    '        if executed > 0:\n            logger.info("Phase 7 Orchestrator: Output %d valid execution targets.", executed)\n'
    + insertion,
)

with open("quant_monitor/main.py", "w", encoding="utf-8") as f:
    f.write(text)
