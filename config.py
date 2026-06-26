# -*- coding: utf-8 -*-
"""Cau hinh DA-OD1RP standalone (KHONG dung DB, KHONG dung Google Sheet)."""
from pathlib import Path
import glob, os
from datetime import date, datetime

# Thu muc chua file tho hang ngay (revenue, remaining_lesson, attendance, leads)
# Mac dinh tro toi Input cua DA1RP; co the copy file tho sang INPUT_DIR rieng cua repo.
_CANDS = [
    Path(r"C:\Users\ASUS\Desktop\Palfish data\Palfish DA Daily update\Input"),
    Path(__file__).resolve().parent / "inputs",
    Path("/sessions/eloquent-keen-dijkstra/mnt/Palfish data/Palfish DA Daily update/Input"),
]
INPUT_DIR = next((p for p in _CANDS if p.exists()), _CANDS[0])

HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "outputs"
STATE_DIR = HERE / "state"
DIM_SALE_CSV = HERE / "dim_sale.csv"           # thay cho Google Sheet dim_sale
SNAPSHOT_PREV = STATE_DIR / "snapshot_prev.csv"  # thay cho snapshot 'hom qua' tu DB
DA1RP_SEED = HERE / "da1rp_remaining_lesson3.csv"  # nguon seed end_date + status_renew tu DA1RP
LAST_STUDY_SEED = HERE / "da1rp_last_study_history.csv"  # lich su remain per UID (cho cohort) - co the thieu
IS_FROZEN_SEED = HERE / "da1rp_is_frozen.csv"  # order_id -> is_frozen (tu raw remaining_lesson, cho Tab 6 bao luu)
for d in (OUTPUT_DIR, STATE_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Tu khoa nhan dien file tho (giong DA1RP)
KEYWORD = {
    "lead_allocation": "all_leads_to_vn_sales_",
    "remaining_lesson": "remaining_lesson__vn__",
    "lead_status": "leads_status_update",
    "revenue_hcm": "HCM Revenue statement",
    "revenue_hn": "SM HANOI daily report",
    "revenue_dn": "Danang revenue",
    "complete_homework_data": "国际化用户课程状态明细表_越南",
}

DANANG_FALLBACK = INPUT_DIR / "Danang revenue & cost statement.xlsx"


def find_latest_files(require_today=False):
    """Tim file moi nhat theo tu khoa. require_today=False de chay duoc voi file cu."""
    files = [f for f in glob.glob(os.path.join(str(INPUT_DIR), "*.*"))
             if f.lower().endswith((".xlsx", ".csv")) and not os.path.basename(f).startswith("~$")]
    today = date.today()
    latest = {}
    for key, kw in KEYWORD.items():
        matched = [f for f in files if kw in os.path.basename(f)]
        if require_today:
            matched = [f for f in matched
                       if datetime.fromtimestamp(os.path.getmtime(f)).date() == today]
        if matched:
            latest[key] = max(matched, key=os.path.getmtime)
    if "revenue_dn" not in latest and DANANG_FALLBACK.exists():
        latest["revenue_dn"] = str(DANANG_FALLBACK)
    return latest
