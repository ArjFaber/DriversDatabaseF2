import asyncio
import csv
import hashlib
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

URL = "https://www.fiaformula2.com/livetiming/index.html"
CSV_FILE = Path("f2_live_dom.csv")


def init_csv():
    if not CSV_FILE.exists():
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "raw_text"])


def save(text):
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.utcnow().isoformat(), text])


def make_hash(text: str) -> str:
    # normalize whitespace so tiny DOM differences don't trigger duplicates
    normalized = " ".join(text.split())
    return hashlib.md5(normalized.encode()).hexdigest()


async def run():
    init_csv()

    print("Launching browser...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=100
        )

        page = await browser.new_page()

        print("Going to page...")

        await page.goto(URL, timeout=60000)

        print("Page loaded (or timeout reached)")

        await page.wait_for_timeout(5000)

        print("Starting scraping loop...")

        last_hash = None  # 👈 key fix

        for i in range(10):
            text = await page.evaluate("document.body.innerText")

            current_hash = make_hash(text)

            print(f"\nSNAPSHOT {i}")

            # ONLY SAVE IF CHANGED
            if current_hash != last_hash:
                print("✔ Change detected → saving")
                save(text)
                last_hash = current_hash
            else:
                print("⏭ No change → skipped")

            await asyncio.sleep(2)

        await browser.close()
    import pandas as pd
    import re


    # Load your original CSV
    source_df = pd.read_csv("f2_live_dom.csv")

    pattern = re.compile(
        r'(\d+)\s+'                      # position
        r'(\d+)\s+'                      # car number
        r'([A-Z]\.[A-Z ]+)\s+'           # driver name
        r'([A-Z0-9\.L]+)\s+'             # gap
        r'([A-Z0-9\.L]+)\s+'             # interval
        r'((?:\d:\d{2}\.\d+)|STOP)\s+'   # lap time
        r'([0-9\.]+|STOP)\s+'
        r'([0-9\.]+|STOP)\s+'
        r'([0-9\.]+)?\s*'
        r'(\d+)?'
    )

    rows = []

    for _, race_row in source_df.iterrows():
        timestamp = race_row["timestamp"]
        raw_text = race_row["raw_text"]

        for match in pattern.finditer(raw_text):
            rows.append({
                "timestamp": timestamp,
                "position": int(match.group(1)),
                "car_number": int(match.group(2)),
                "driver": match.group(3).strip(),
                "gap": match.group(4),
                "interval": match.group(5),
                "lap_time": match.group(6),
                "sector1": match.group(7),
                "sector2": match.group(8),
                "sector3": match.group(9),
                "pit_stops": match.group(10)
            })

    laps_df = pd.DataFrame(rows)
    laps_df.columns = [
    "timestamp",
    "position",
    "car_number",
    "driver",
    "gap",
    "interval",
    "lap_time",
    "sector1",
    "sector2",
    "sector3",
    "pit_stops"
]

    laps_df.to_csv(
        "laps_data.csv",
        mode="a",          # append mode
        header=False,      # don't write header again
        index=False
    )
    print("DONE")


asyncio.run(run())

