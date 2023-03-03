import glob
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Tuple
import requests

import pandas as pd


BINANCE_DATA_BASE = "https://data.binance.vision/data/spot/monthly/klines/{symbol}/{freq}/{symbol}-{freq}-{year}-{month}.zip"
BINANCE_FUTURE_BASE = "https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/{freq}/{symbol}-{freq}-{year}-{month}.zip"
KLINE_COL = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_asset_vol",
    "num_trades",
    "taker_buy_base",
    "take_buy_quote",
    "_",
]
ASSET_MAP = {
    "spot": BINANCE_DATA_BASE,
    "future": BINANCE_FUTURE_BASE,
}


def gen_urls(
    symbol: str, freq: str, start: int, end: int, base: str, type: str = "spot"
):
    """ get all the urls of the history file """
    urls = []  # (filename, url)
    base_dir = f"{base}/{symbol}"
    for year in range(start, end + 1):
        for month in range(1, 13):
            month_str = "{:02d}".format(month)
            url_base = ASSET_MAP[type]
            url = url_base.format(symbol=symbol, freq=freq, year=year, month=month_str)
            fullpath = f"{base_dir}/{freq}/{url.split('/')[-1]}"
            urls.append((fullpath, url))

    return urls


def download_task(info: Tuple[str, str]):
    """ download files
    
    Parameters
    ----------
    info: (the file path to downloand to, the remote file location)
    """
    fullpath, url = info
    if os.path.exists(fullpath):
        return

    os.makedirs(os.path.dirname(fullpath), exist_ok=True)
    res = requests.get(url)
    if res.status_code == 200:
        print(f"Downloading {fullpath}")
        with open(fullpath, "wb") as f:
            f.write(res.content)


## API
def download(
    symbol: str,
    freq: str,
    start: int,
    end: int,
    base: str,
    max_worker=5,
    type: str = "spot",
):
    """Download history bar data
    note: it won't download duplicated files
    """
    info = gen_urls(
        symbol=symbol, freq=freq, start=start, end=end, base=base, type=type
    )
    with ThreadPoolExecutor(max_workers=max_worker) as executor:
        for url in info:
            executor.submit(download_task, info=url)


def load_raw_zip(symbol: str, freq: str, base: str) -> pd.DataFrame:
    """ Load history zip files into pandas """
    path = f"{base}/{symbol}/{freq}/*.zip"
    files = glob.glob(path)
    dfs = []
    for f in files:
        print(f"Loading {f.split('/')[-1]} ...")
        try:
            df = pd.read_csv(f, header=None, names=KLINE_COL)
            df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
            df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
        except ValueError:
            df = pd.read_csv(f)
            df.columns = KLINE_COL
            df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
            df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")

        df = df.set_index("open_time", drop=True)
        dfs.append(df)

    res = pd.concat(dfs).sort_index()

    return res


def parquet_file(symbol: str, freq: str, start: int, end: int, base: str):
    return f"{base}/{symbol}/agg/{freq}/{start}-{end}-{freq}-{symbol}.parquet"



if __name__ == "__main__":
    # Download raw zip files and dump a single parquet file
    base = "./future"  # change the target folder to host the files
    start = 2023
    end = 2023
    freq = "5m"
    # universe = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "BNBUSDT", "ADAUSDT", "DOGEUSDT"]
    universe = ["BTCUSDT"]
    for symbol in universe:
        download(symbol, freq, start, end, base, max_worker=5, type="future")
        # Dump parquet file
        df = load_raw_zip(symbol, freq, base)
        file_path = f"{symbol}/agg/{freq}/{start}-{end}-{freq}-{symbol}.parquet"
        parquet_path = (
            f"{base}/{file_path}"
        )
        os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
        df.to_parquet(parquet_path)

    # Load paruqet history data
    btc = pd.read_parquet(parquet_file("BTCUSDT", freq, start, end, base))
    print(btc)