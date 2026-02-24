#!/usr/bin/env python3
"""Setup Appwrite database and collections.

Run with Doppler:
    doppler run -- uv run python scripts/setup_appwrite.py
"""

from __future__ import annotations

import os
import sys

from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
from appwrite.exception import AppwriteException

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
        print(f"    ✓ Created attribute: {name} ({attr_type})")
    except AppwriteException as e:
        if "already exists" in str(e).lower():
            print(f"    → Attribute exists: {name}")
        else:
            print(f"    ✗ Error creating {name}: {e}")


def main() -> int:
    """Create database and collections."""
    # Get secrets from environment (Doppler injects these)
    endpoint = os.environ.get("APPWRITE_ENDPOINT")
    project_id = os.environ.get("APPWRITE_PROJECT_ID")
    api_key = os.environ.get("APPWRITE_API_KEY")

    if not all([endpoint, project_id, api_key]):
        print("ERROR: Missing Appwrite credentials. Run with: doppler run -- ...")
        return 1

    print(f"Connecting to Appwrite at {endpoint}")
    print(f"Project: {project_id}")
    print()

    # Initialize client
    client = Client()
    client.set_endpoint(endpoint)
    client.set_project(project_id)
    client.set_key(api_key)

    databases = Databases(client)

    # Create database
    print(f"Creating database: {DATABASE_NAME}")
    try:
        databases.create(database_id=DATABASE_ID, name=DATABASE_NAME)
        print(f"✓ Database created: {DATABASE_ID}")
    except AppwriteException as e:
        if "already exists" in str(e).lower():
            print(f"→ Database exists: {DATABASE_ID}")
        else:
            print(f"✗ Error: {e}")
            return 1

    print()

    # Create collections
    for collection_id, config in COLLECTIONS.items():
        print(f"Creating collection: {config['name']}")
        try:
            databases.create_collection(
                database_id=DATABASE_ID,
                collection_id=collection_id,
                name=config["name"],
            )
            print(f"  ✓ Collection created: {collection_id}")
        except AppwriteException as e:
            if "already exists" in str(e).lower():
                print(f"  → Collection exists: {collection_id}")
            else:
                print(f"  ✗ Error: {e}")
                continue

        # Create attributes
        for attr in config["attributes"]:
            create_attribute(databases, DATABASE_ID, collection_id, attr)

        print()

    print("=" * 50)
    print("Appwrite setup complete!")
    print(f"Database: {DATABASE_ID}")
    print(f"Collections: {len(COLLECTIONS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
