# -*- coding: utf-8 -*-
"""Tai lai dim_sale.csv + dim_channel.csv tu Google Sheet [PF] Data Dimension.
Chay khi danh sach sale/kenh thay doi:  python fetch_dims.py
(Sheet o che do 'anyone with link' nen khong can dang nhap.)
"""
import urllib.request
from pathlib import Path

SHEET_ID = "1mCDRdmfpxNyYrn0GoAPrTH6uOClWtI5SYB13cNDsHXM"
HERE = Path(__file__).resolve().parent
TABS = {"dim_sale": HERE / "dim_sale.csv", "dim_channel": HERE / "dim_channel.csv"}


def main():
    for tab, out in TABS.items():
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={tab}"
        with urllib.request.urlopen(url, timeout=60) as r:
            data = r.read()
        out.write_bytes(data)
        print(f"saved {out.name} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
