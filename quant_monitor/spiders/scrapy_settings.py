"""Scrapy settings for Zyte Scrapy Cloud deployment.

These settings are used when spiders run on Scrapy Cloud.
Local testing: scrapy crawl <spider_name> -s SETTINGS_MODULE=quant_monitor.spiders.scrapy_settings
"""

# Scrapy settings
BOT_NAME = "quant_monitor"
SPIDER_MODULES = ["quant_monitor.spiders"]
NEWSPIDER_MODULE = "quant_monitor.spiders"

# Obey robots.txt
ROBOTSTXT_OBEY = True

# Rate limiting — be a good citizen
DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# User agent (SEC EDGAR requires identification)
USER_AGENT = "QuantMonitor/1.0 (Academic Research; Hult Business School)"

# Item pipelines — push to Appwrite
ITEM_PIPELINES = {
    "quant_monitor.spiders.pipelines.AppwritePipeline": 300,
}

# Logging
LOG_LEVEL = "INFO"

# Retry
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# AutoThrottle (Scrapy Cloud)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
