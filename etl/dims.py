# -*- coding: utf-8 -*-
"""Map team (dim_sale) + channel (dim_channel) tu CSV local (thay Google Sheet)."""
import re
import pandas as pd
from unidecode import unidecode
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DIM_SALE = HERE / "dim_sale.csv"
DIM_CHANNEL = HERE / "dim_channel.csv"


def _norm_name(s):
    s = unidecode(str(s)) if s is not None else ""
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


# Map Co so -> team (GIONG HET DA1RP: np.select conditions)
COSO_TO_TEAM = {
    "HN-An Bình": "Offline Team HaNoi",
    "HN-Linh Đàm": "Offline Team HaNoi",
    "HN-Team 2": "Inhouse 2",
    "HN-Inhouse": "Inhouse 1",
    "HCM": "Ho Chi Minh",
    "IND": "IND",
    "DN": "DN",
}


def load_team_map():
    """dict: ten_sale_chuan -> team (suy tu 'Cơ sở' giong DA1RP)."""
    if not DIM_SALE.exists():
        return {}
    d = pd.read_csv(DIM_SALE, dtype=str).fillna("")
    m = {}
    for _, r in d.iterrows():
        key = _norm_name(r["Tên trên CRM"])
        coso = (r.get("Cơ sở") or "").strip()
        team = COSO_TO_TEAM.get(coso, "Other")
        if key:
            m[key] = team
    return m


def map_team(name_series, team_map=None):
    team_map = team_map or load_team_map()
    return name_series.map(lambda x: team_map.get(_norm_name(x), "Other"))


def load_channel_map():
    """dict: channel_id(str) -> channel_name."""
    if not DIM_CHANNEL.exists():
        return {}
    d = pd.read_csv(DIM_CHANNEL, dtype=str).fillna("")
    out = {}
    for _, r in d.iterrows():
        cid = re.sub(r"[^\d-]", "", str(r["channel"]))  # bo dau phay phan cach nghin
        if cid:
            out[cid] = r["channel_name"]
    return out
