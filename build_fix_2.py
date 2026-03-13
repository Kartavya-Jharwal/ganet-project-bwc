with open("quant_monitor/main.py", encoding="utf-8") as f:
    text = f.read()

import re

text = re.sub(r'    try:\n\n    # Optional: run spiders.*    except \(KeyboardInterrupt, SystemExit\):',
r'''    # Optional: run spiders every hour for supplemental data
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
    except (KeyboardInterrupt, SystemExit):''', text, flags=re.DOTALL)

with open("quant_monitor/main.py", "w", encoding="utf-8") as f:
    f.write(text)