with open("quant_monitor/main.py", encoding="utf-8") as f:
    text = f.read()

func_to_add = '''

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
'''

if "def run_spiders()" not in text:
    text = text.replace('def main() -> None:', func_to_add + '\n\ndef main() -> None:')

sched_add = '''
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
'''

if "use_local_spiders =" not in text:
    text = text.replace('    scheduler.start()', sched_add + '\n    scheduler.start()')

with open("quant_monitor/main.py", "w", encoding="utf-8") as f:
    f.write(text)
