import csv
import httpx
import pandas as pd
from datetime import datetime
from typing import List, Dict

from dagster import solid, pipeline, AssetMaterialization, EventMetadata, Output, ModeDefinition, fs_io_manager, OutputDefinition
from pathlib import Path


@solid
def fetch_power_to_choose_plans(context):
    cookies = {
        'PowerToChoose.CurrentLanguage': 'en-US',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'http://www.powertochoose.org',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Referer': 'http://www.powertochoose.org/en-us/Plan/Results',
        'Upgrade-Insecure-Requests': '1',
    }

    with httpx.stream(
        "POST",
        'http://www.powertochoose.org/en-us/Plan/ExportToCsv',
        headers=headers,
        cookies=cookies,
        timeout=30,
    ) as response:
        data = [row for row in csv.DictReader(response.iter_lines())]
    context.log.info(f"Fetched {len(data)} rows.")
    return data


@solid
def store_csv_dict_as_csv(context, csv_dict: List[Dict]):
    dt = datetime.now()
    p = Path(".") / "output" 
    p.mkdir(parents=True, exist_ok=True)
    filename = f"{dt:%Y-%m-%d_%H:%M:%S}_power_to_choose_{context.run_id}"
    filepath = p / filename
    with open(filepath, "w") as f:
        headers = csv_dict[0].keys()
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        writer.writerows(csv_dict)
    
    yield AssetMaterialization(
        asset_key="power_to_choose_csv",
        description="Pull of Power to Choose data",
        metadata={
            "power_to_choose_csv_path": EventMetadata.path(str(filepath.resolve()))
        },
    )

    yield Output(None)


@solid
def clean(csv_dict: List[Dict]) -> pd.DataFrame:
    df: pd.DataFrame = pd.DataFrame(csv_dict)
    df.columns = df.columns.str.strip("[]")
    df = df.drop(df[df["idKey"] == "END OF FILE"].index)
    return df


# supplying a fs_io_manager allows re-runs from dagit b/c Dagster will store pickles of all intermediate results
@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={
                "io_manager": fs_io_manager.configured({"base_dir": str(Path(".", "fs_io"))})
            }
        )
    ]
)
def power_to_choose():
    csv_dict = fetch_power_to_choose_plans() 
    store_csv_dict_as_csv(csv_dict)
    clean(csv_dict)
