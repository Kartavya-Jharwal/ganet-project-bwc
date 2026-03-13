with open("quant_monitor/main.py", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = lines[:-30]
tail_replacement = """        run_signal_cycle,
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
"""

with open("quant_monitor/main.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
    f.write(tail_replacement)
