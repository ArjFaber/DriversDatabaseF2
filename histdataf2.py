import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE_URL = "https://www.fiaformula2.com/Results?raceid={}"

results = []

print("Starting scrape...")

for race_id in range(972, 1171):  # adjust range
    url = BASE_URL.format(race_id)

    print(f"\nChecking race_id={race_id} -> {url}")

    try:
        response = requests.get(url, timeout=10)
        print(f"Response status: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed for race {race_id}: {e}")
        continue

    if response.status_code != 200:
        print(f"Skipping race {race_id}: status code {response.status_code}")
        continue

    if "No results found" in response.text:
        print(f"No results for race {race_id}")
        continue

    print(f"Found race {race_id}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Example only - actual selectors depend on page structure
    tables = soup.find_all("table")
    print(f"Found {len(tables)} tables on page")

    if not tables:
        print(f"No tables found for race {race_id}")

    for table_index, table in enumerate(tables, start=1):
        rows = table.find_all("tr")
        print(f"  Table {table_index}: {len(rows)} rows")

        for row_index, row in enumerate(rows[1:], start=1):
            cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]

            if cols:
                print(f"    Row {row_index}: extracted {len(cols)} columns")
                results.append([race_id] + cols)

    print(f"Current total records collected: {len(results)}")

print("\nScraping complete.")
print(f"Total rows collected: {len(results)}")


df = pd.DataFrame(results)
df.columns = ['Event_ID', 'Number/Driver/Team', 'Laps', 'Time', 'Gap', 'Int.', 'Kph', 'Best', 'Lap']
print("Saving results to formula2_results.csv...")
df.to_csv("formula2_results.csv", index=False)

print("Done!")
