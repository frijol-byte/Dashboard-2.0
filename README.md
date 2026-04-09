#!/usr/bin/env python3
"""
build_db.py — Reads all CSVs in data/ and loads them into public/cfps.db

Directory conventions:
  data/results/   → CSVs go into the "results" table (append all files)
  data/layouts/   → CSVs go into the "layouts" table (append all files)

Run manually:   python scripts/build_db.py
Run in CI:      see .gitlab-ci.yml
"""

import sqlite3
import csv
import os
import glob
import sys

DB_PATH = os.path.join("public", "cfps.db")
DATA_DIR = "data"

# Map subfolder names to table names
TABLE_MAP = {
    "results": "results",
    "layouts": "layouts",
}

# Lot tracker CSVs: each file in data/lots/ becomes its own table
# e.g. data/lots/fermentation.csv → table "lot_fermentation"
LOTS_DIR = os.path.join(DATA_DIR, "lots")


def infer_type(value):
    """Try to cast a string value to int, then float, else keep as text."""
    try:
        return int(value)
    except (ValueError, TypeError):
        pass
    try:
        return float(value)
    except (ValueError, TypeError):
        pass
    return value


def load_csv(filepath):
    """Read a CSV file and return (headers, rows)."""
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = [h.strip().lower().replace(" ", "_") for h in next(reader)]
        rows = []
        for row in reader:
            if len(row) != len(headers):
                continue
            rows.append([infer_type(v.strip()) for v in row])
    return headers, rows


def create_table(cursor, table_name, headers, rows):
    """Create table if not exists, insert rows."""
    # Infer column types from first data row
    type_map = {int: "INTEGER", float: "REAL", str: "TEXT"}
    if rows:
        col_types = [type_map.get(type(v), "TEXT") for v in rows[0]]
    else:
        col_types = ["TEXT"] * len(headers)

    cols_def = ", ".join(
        f'"{h}" {t}' for h, t in zip(headers, col_types)
    )

    cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({cols_def})')

    # Check existing columns — if new CSV has columns the table doesn't,
    # add them (handles schema evolution across experiments)
    cursor.execute(f'PRAGMA table_info("{table_name}")')
    existing_cols = {row[1] for row in cursor.fetchall()}
    for h, t in zip(headers, col_types):
        if h not in existing_cols:
            cursor.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{h}" {t}')

    placeholders = ", ".join("?" * len(headers))
    col_names = ", ".join(f'"{h}"' for h in headers)
    cursor.executemany(
        f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})',
        rows,
    )


def main():
    os.makedirs("public", exist_ok=True)

    # Remove old DB so we rebuild fresh each time
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    total_rows = 0

    for subfolder, table_name in TABLE_MAP.items():
        folder_path = os.path.join(DATA_DIR, subfolder)
        if not os.path.isdir(folder_path):
            print(f"  Skipping {folder_path}/ (not found)")
            continue

        csv_files = sorted(glob.glob(os.path.join(folder_path, "*.csv")))
        if not csv_files:
            print(f"  No CSVs in {folder_path}/")
            continue

        for csv_path in csv_files:
            filename = os.path.basename(csv_path)
            headers, rows = load_csv(csv_path)

            # Add a source_file column so you know which CSV each row came from
            headers.append("source_file")
            for row in rows:
                row.append(filename)

            create_table(cursor, table_name, headers, rows)
            total_rows += len(rows)
            print(f"  {table_name} ← {filename} ({len(rows)} rows)")

    conn.commit()

    # ── Lot tracker CSVs ─────────────────────────────────────────────────────
    if os.path.isdir(LOTS_DIR):
        lot_csvs = sorted(glob.glob(os.path.join(LOTS_DIR, "*.csv")))
        for csv_path in lot_csvs:
            filename = os.path.basename(csv_path)
            table_name = "lot_" + os.path.splitext(filename)[0]
            headers, rows = load_csv(csv_path)
            create_table(cursor, table_name, headers, rows)
            total_rows += len(rows)
            print(f"  {table_name} ← {filename} ({len(rows)} rows)")
        conn.commit()
    else:
        print(f"  Skipping {LOTS_DIR}/ (not found)")

    # Print summary
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = [r[0] for r in cursor.fetchall()]
    for table_name in all_tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            count = cursor.fetchone()[0]
            print(f"  Table '{table_name}': {count} total rows")
        except sqlite3.OperationalError:
            print(f"  Table '{table_name}': not created (no data)")

    conn.close()
    db_size = os.path.getsize(DB_PATH) / 1024
    print(f"\n  Database: {DB_PATH} ({db_size:.0f} KB)")
    print(f"  Total rows inserted: {total_rows}")


if __name__ == "__main__":
    main()
