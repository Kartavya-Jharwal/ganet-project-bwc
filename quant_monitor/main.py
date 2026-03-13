"""APScheduler entry point — orchestrates the 15-minute signal generation cycle.

Run locally:  doppler run -- uv run python -m quant_monitor.main
Run on Heroku: see Procfile (worker dyno)
"""

from __future__ import annotations

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_signal_cycle() -> None:
    """Execute one full signal generation cycle.

    1. Fetch data (prices, macro, news, fundamentals)
    2. Compute features (MA matrix, volatility, sentiment)
    3. Run models (technical, macro, sentiment, fundamental)
    4. Classify regime
    5. Fuse signals
    6. Risk-check + optimization
    7. Store results in Appwrite
    8. Dispatch alerts if thresholds crossed
    """
    from quant_monitor.agent.fusion import SignalFusion
    from quant_monitor.config import cfg
    from quant_monitor.data.pipeline import DataPipeline
    from quant_monitor.features.sentiment_features import SentimentFeatureEngine
    from quant_monitor.features.volatility import (
        classify_regime,
        hurst_exponent,
        realized_volatility,
        volatility_percentile,
    )
    from quant_monitor.models.fundamental import FundamentalModel
    from quant_monitor.models.macro import MacroModel
    from quant_monitor.models.sentiment import SentimentModel
    from quant_monitor.models.technical import TechnicalModel

    pipeline = DataPipeline()
    tickers = cfg.tickers

    logger.info("── Signal cycle starting for %d tickers ──", len(tickers))

    try:
        # 1. Fetch data
        prices = pipeline.fetch_prices(tickers)
        macro = pipeline.fetch_macro()
        news = pipeline.fetch_news(tickers)
        fundamentals = pipeline.fetch_fundamentals(tickers)

        # 2. Classify volatility regime
        spy_prices = prices.loc["SPY"] if "SPY" in prices.index.get_level_values(0) else None
        if spy_prices is not None and len(spy_prices) > 200:
            returns = spy_prices["close"].pct_change().dropna()
            vol = realized_volatility(returns)
            vol_pct = volatility_percentile(vol.dropna())
            hurst = hurst_exponent(spy_prices["close"])
            vix = macro.get("vix", 20.0)
            regime = str(classify_regime(vol.iloc[-1], vol_pct.iloc[-1], hurst, vix))
        else:
            regime = "LOW_VOL_TREND"  # safe default

        # 3. Run models
        tech_model = TechnicalModel()
        macro_model = MacroModel()
        sent_model = SentimentModel()
        fund_model = FundamentalModel()

        tech_scores = tech_model.score_all(
            {t: prices.loc[t] for t in tickers if t in prices.index.get_level_values(0)}
        )
        macro_score = macro_model.score(macro)
        macro_regime = macro_model.classify_regime(macro)

        # Sentiment: score headlines per ticker
        sent_engine = SentimentFeatureEngine()
        sent_scores = {}
        for ticker in tickers:
            ticker_news = news.get(ticker, [])
            if ticker_news:
                headlines = [n.get("title", "") for n in ticker_news if n.get("title")]
                if headlines:
                    scored = sent_engine.score_headlines(headlines)
                    import pandas as pd
                    scored_df = pd.DataFrame(scored)
                    if not scored_df.empty:
                        sent_scores[ticker] = sent_model.score(scored_df)
                        continue
            sent_scores[ticker] = 0.0

        # Fundamental scores (simplified for scheduler)
        fund_scores = {t: 0.0 for t in tickers}  # placeholder until pipeline provides sector data

        # 4. Fuse signals
        fusion = SignalFusion()
        fused = fusion.fuse_all(tech_scores, fund_scores, sent_scores, macro_score, regime)

        # 5. Risk-check + optimization
        import pandas as pd

        from quant_monitor.agent.optimizer import PortfolioOptimizer
        from quant_monitor.agent.risk_manager import RiskManager
        
        optimizer = PortfolioOptimizer()
        risk_manager = RiskManager()
        
        # Build views from fused signal scores
        views = {}
        view_confidences = {}
        for t, res in fused.items():
            # Convert action to expected return (-10% to +10%)
            score = res["fused_score"]
            if res["action"] == "BUY":
                views[t] = abs(score) * 0.1
            elif res["action"] == "SELL":
                views[t] = -abs(score) * 0.1
            else:
                views[t] = 0.0
            view_confidences[t] = res["confidence"]
            
        # Get latest prices for optimization
        latest_prices = {}
        for t in tickers:
            if t in prices.index.get_level_values(0):
                latest_prices[t] = prices.loc[t, "close"].iloc[-1]
        
        current_prices_series = pd.Series(latest_prices)
        current_positions = {}  # Mock empty portfolio for now
        current_weights = {t: 0.0 for t in tickers}
        
        # Kill switch check
        kills = risk_manager.check_kill_switch(current_positions, latest_prices)
        if kills:
            logger.critical("Kill switch triggered for %d positions", len(kills))
            for k in kills:
                views[k["ticker"]] = -1.0  # Force dump
        
        # Compute target weights using Black-Litterman
        target_weights = optimizer.compute_target_weights(
            current_prices=current_prices_series,
            views=views,
            view_confidences=view_confidences
        )
        
        # Generate rebalancing trade instructions
        proposed_trades = optimizer.compute_rebalance_trades(
            current_weights=current_weights,
            target_weights=target_weights,
            drift_threshold=0.01
        )
        
        # Validate proposed trades against risk limits
        validated_trades = risk_manager.validate_trades(
            proposed_trades=proposed_trades,
            current_positions=current_positions,
            regime=regime
        )

        # 6. Log results
        for ticker, result in fused.items():
            if result["action"] != "HOLD":
                logger.info(
                    "SIGNAL: %s → %s (score=%.3f, confidence=%.3f, dominant=%s)",
                    ticker, result["action"], result["fused_score"],
                    result["confidence"], result["dominant_model"],
                )

        # Log planned executions
        executed = 0
        for trade in validated_trades:
            if trade.get("rejected_reason"):
                logger.warning("REJECTED TRADE %s: %s", trade["ticker"], trade["rejected_reason"])
            else:
                executed += 1
                logger.info(
                    "EXECUTE TRADE: %s → Target: %.1f%% (Delta: %+.1f%%)", 
                    trade["ticker"], trade["target_weight"] * 100, trade.get("delta", 0) * 100
                )
        
        if executed > 0:
            logger.info("Phase 7 Orchestrator: Output %d valid execution targets.", executed)

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
            from quant_monitor.features.volatility import hurst_exponent, realized_volatility
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

        from quant_monitor.agent.alerts import AlertDispatcher, AlertPriority, AlertType
        dispatcher = AlertDispatcher()

        for ticker, result in fused.items():
            if result["action"] in ("BUY", "SELL"):
                msg = (
                    f"<b>{ticker}</b>: {result['action']}\n"
                    f"Score: {result['fused_score']:.3f} | Confidence: {result['confidence']:.3f}\n"
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


        logger.info(
            "── Signal cycle complete | Regime: %s | Macro regime: %s ──",
            regime, macro_regime,
        )

    except Exception as e:
        logger.error("Signal cycle failed: %s", e, exc_info=True)




def run_spiders() -> None:
    """Run Scrapy spiders locally (alternative to Scrapy Cloud deployment).

    This is optional — spiders can also run on Zyte Scrapy Cloud.
    When running locally, results go through AppwritePipeline → Appwrite.
    """
    try:
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings

        from quant_monitor.spiders.google_rss_spider import GoogleRssSpider
        from quant_monitor.spiders.sec_edgar_spider import SecEdgarSpider
        from quant_monitor.spiders.yfinance_spider import YfinanceSpider

        settings = get_project_settings()
        settings.setmodule("quant_monitor.spiders.scrapy_settings")

        process = CrawlerProcess(settings)
        process.crawl(GoogleRssSpider)
        process.crawl(SecEdgarSpider)
        # YfinanceSpider only if Massive is unavailable
        from quant_monitor.data.sources.massive_feed import get_massive_feed
        if not get_massive_feed().is_available:
            process.crawl(YfinanceSpider)

        process.start(stop_after_crawl=True)
        logger.info("Spider run complete")
    except Exception as e:
        logger.error("Spider run failed: %s", e, exc_info=True)


def main() -> None:
    """Start the portfolio monitoring scheduler."""
    from quant_monitor.config import cfg

    logger.info("Quant Portfolio Monitor starting")
    logger.info("Tracking %d positions | Benchmark: %s", len(cfg.tickers), cfg.benchmark)
    logger.info("Valuation date: %s | Sunset: %s", cfg.valuation_date, cfg.sunset_date)

    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.interval import IntervalTrigger

    scheduler = BlockingScheduler()

    interval = cfg.project.get("rebalance_interval_minutes", 15)

    # Run immediately on startup
    run_signal_cycle()

    # Then every N minutes
    scheduler.add_job(
        run_signal_cycle,
        trigger=IntervalTrigger(minutes=interval),
        id="signal_cycle",
        name="Signal Generation Cycle",
        replace_existing=True,
    )

    logger.info("Scheduler started — running every %d minutes", interval)

    # Optional: run spiders every hour for supplemental data
    use_local_spiders = getattr(cfg, "scrapy_cloud", {}).get("local_spiders", False)
    if use_local_spiders:
        scheduler.add_job(
            run_spiders,
            trigger=IntervalTrigger(minutes=getattr(cfg, "scrapy_cloud", {}).get("schedule_off_hours_minutes", 60)),
            id="spider_run",
            name="Scrapy Spider Run",
            replace_existing=True,
        )
        logger.info("Local spider scheduling enabled — every %d min", getattr(cfg, "scrapy_cloud", {}).get("schedule_off_hours_minutes", 60))

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    main()
