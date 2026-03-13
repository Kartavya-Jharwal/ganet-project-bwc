#!/usr/bin/env python3
"""Setup Appwrite database and collections.

Run with Doppler:
    doppler run -- uv run python scripts/setup_appwrite.py
"""

from __future__ import annotations

import os
import sys

from appwrite.client import Client
from appwrite.exception import AppwriteException
from appwrite.services.databases import Databases
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

console = Console()

# Database configuration
DATABASE_ID = "quant_db"
DATABASE_NAME = "Quant Monitor Database"

# Collection definitions with attributes
COLLECTIONS = {
    "portfolio_snapshots": {
        "name": "Portfolio Snapshots",
        "attributes": [
            ("timestamp", "datetime", True),
            ("total_value", "float", True),
            ("cash", "float", True),
            ("pnl_day", "float", True),
            ("pnl_total", "float", True),
            ("regime", "string", True, 50),
            ("beta", "float", True),
        ],
    },
    "position_snapshots": {
        "name": "Position Snapshots",
        "attributes": [
            ("timestamp", "datetime", True),
            ("ticker", "string", True, 10),
            ("qty", "integer", True),
            ("price", "float", True),
            ("value", "float", True),
            ("weight", "float", True),
            ("pnl_day", "float", True),
            ("pnl_total", "float", True),
        ],
    },
    "signals": {
        "name": "Signals",
        "attributes": [
            ("timestamp", "datetime", True),
            ("ticker", "string", True, 10),
            ("technical_score", "float", True),
            ("fundamental_score", "float", True),
            ("sentiment_score", "float", True),
            ("macro_score", "float", True),
            ("fused_score", "float", True),
            ("confidence", "float", True),
            ("action", "string", True, 20),
            ("regime", "string", True, 50),
            ("dominant_model", "string", False, 20),
        ],
    },
    "alerts": {
        "name": "Alerts",
        "attributes": [
            ("timestamp", "datetime", True),
            ("ticker", "string", False, 10),
            ("alert_type", "string", True, 30),
            ("message", "string", True, 500),
            ("severity", "string", True, 10),
            ("dispatched", "boolean", True),
        ],
    },
    "regime_history": {
        "name": "Regime History",
        "attributes": [
            ("timestamp", "datetime", True),
            ("regime", "string", True, 50),
            ("vix", "float", True),
            ("hurst", "float", True),
            ("vol_percentile", "float", True),
        ],
    },
    "scraped_data": {
        "name": "Scraped Data",
        "attributes": [
            ("timestamp", "datetime", True),
            ("source", "string", True, 30),
            ("ticker", "string", False, 10),
            ("data_type", "string", True, 30),
            ("content", "string", True, 10000),
            ("url", "string", False, 500),
        ],
    },
    "eod_price_matrix": {
        "name": "EOD Price Matrix",
        "attributes": [
            ("timestamp", "datetime", True),
            ("ticker", "string", True, 10),
            ("close", "float", True),
        ],
    },
    "live_spy_proxy": {
        "name": "Live SPY Proxy",
        "attributes": [
            ("timestamp", "datetime", True),
            ("price", "float", True),
        ],
    },
    "correlations_cache": {
        "name": "Correlations Cache",
        "attributes": [
            ("timestamp", "datetime", True),
            ("nodes", "string", True, 10000),       # JSON encoded nodes
            ("edges", "string", True, 10000),       # JSON encoded edgelist
        ],
    },
}


def create_attribute(
    databases: Databases,
    database_id: str,
    collection_id: str,
    attr: tuple,
) -> None:
    """Create a single attribute based on type."""
    name = attr[0]
    attr_type = attr[1]
    required = attr[2]
    size = attr[3] if len(attr) > 3 else None

    try:
        if attr_type == "string":
            databases.create_string_attribute(
                database_id=database_id,
                collection_id=collection_id,
                key=name,
                size=size or 255,
                required=required,
            )
        elif attr_type == "integer":
            databases.create_integer_attribute(
                database_id=database_id,
                collection_id=collection_id,
                key=name,
                required=required,
            )
        elif attr_type == "float":
            databases.create_float_attribute(
                database_id=database_id,
                collection_id=collection_id,
                key=name,
                required=required,
            )
        elif attr_type == "boolean":
            databases.create_boolean_attribute(
                database_id=database_id,
                collection_id=collection_id,
                key=name,
                required=required,
            )
        elif attr_type == "datetime":
            databases.create_datetime_attribute(
                database_id=database_id,
                collection_id=collection_id,
                key=name,
                required=required,
            )
        console.print(f"    [green]Created attribute[/green]: {name} ({attr_type})")
    except AppwriteException as e:
        if "already exists" in str(e).lower():
            console.print(f"    [yellow]Attribute exists[/yellow]: {name}")
        else:
            console.print(f"    [red]Error creating {name}[/red]: {e}")


def main() -> int:
    """Create database and collections."""
    # Get secrets from environment (Doppler injects these)
    endpoint = os.environ.get("APPWRITE_ENDPOINT")
    project_id = os.environ.get("APPWRITE_PROJECT_ID")
    api_key = os.environ.get("APPWRITE_API_KEY")

    if not all([endpoint, project_id, api_key]):
        console.print(
            "[red]ERROR[/red]: Missing Appwrite credentials. Run with: doppler run -- ..."
        )
        return 1

    console.print(f"Connecting to Appwrite at [cyan]{endpoint}[/cyan]")
    console.print(f"Project: [cyan]{project_id}[/cyan]\n")

    # Initialize client
    client = Client()
    client.set_endpoint(endpoint)
    client.set_project(project_id)
    client.set_key(api_key)

    databases = Databases(client)

    # Create database
    console.print(f"Creating database: {DATABASE_NAME}")
    try:
        databases.create(database_id=DATABASE_ID, name=DATABASE_NAME)
        console.print(f"[green]Database created[/green]: {DATABASE_ID}")
    except AppwriteException as e:
        if "already exists" in str(e).lower():
            console.print(f"[yellow]Database exists[/yellow]: {DATABASE_ID}")
        else:
            console.print(f"[red]Error[/red]: {e}")
            return 1

    console.print()

    # Create collections
    total_attrs = sum(len(config["attributes"]) for config in COLLECTIONS.values())
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Creating collections and attributes", total=total_attrs)

        for collection_id, config in COLLECTIONS.items():
            progress.update(task, description=f"Collection: {config['name']}")
            try:
                databases.create_collection(
                    database_id=DATABASE_ID,
                    collection_id=collection_id,
                    name=config["name"],
                )
                console.print(f"  [green]Collection created[/green]: {collection_id}")
            except AppwriteException as e:
                if "already exists" in str(e).lower():
                    console.print(f"  [yellow]Collection exists[/yellow]: {collection_id}")
                else:
                    console.print(f"  [red]Collection error[/red]: {e}")
                    progress.advance(task, len(config["attributes"]))
                    continue

            for attr in config["attributes"]:
                create_attribute(databases, DATABASE_ID, collection_id, attr)
                progress.advance(task)

    console.print("=" * 50)
    console.print("[green]Appwrite setup complete![/green]")
    console.print(f"Database: {DATABASE_ID}")
    console.print(f"Collections: {len(COLLECTIONS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
