# -*- coding: utf-8 -*-
"""Stage 1 - Ingest local (revenue 3 vung + remaining_lesson). Port tu DA1RP, bo DB/gsheet."""
import re
import pandas as pd
import numpy as np
from unidecode import unidecode
import io, time, zipfile


def _read_excel_robust(path, sheet_name=0, tries=6):
    """Doc Excel co retry: mount doi khi tra byte loi -> doc lai tu bytes da xac thuc zip."""
    last = None
    for k in range(tries):
        try:
            raw = open(path, "rb").read()
            if not zipfile.is_zipfile(io.BytesIO(raw)):
                raise OSError("zip chua hop le (mount chap chon)")
            return pd.read_excel(io.BytesIO(raw), sheet_name=sheet_name)
        except Exception as e:
            last = e
            time.sleep(1.0)
    raise last

SOURCE_MAP = {
    'Lives': 'Lives', '公海': 'Oversea', '广告': 'Online Marketing', '转介绍': 'Refer',
    '续费': 'Renew', 'Offline': 'Offline', 'Other': 'Other', 'Refer': 'Refer',
    'Booth': 'Booth', 'Resell': 'Renew', 'Livestream': 'Livestream', 'GD': 'Database',
    'PNS': 'PNS', 'KET': 'KET',
}


def calculate_total_lessons(text):
    if pd.isna(text):
        return 0
    parts = str(text).split('-', 1)
    if len(parts) < 2:
        return 0
    return sum(int(n) for n in re.findall(r'\d+', parts[1]))


def _clean_uid_13(series):
    s = series.astype(str)
    mask = (s.str.len() == 13) & (s.str.startswith('3'))
    s = s.where(~mask, s.str[1:])
    return pd.to_numeric(s, errors='coerce').astype('Int64')


def load_revenue(latest):
    hcm = _read_excel_robust(latest["revenue_hcm"], 'REVENUE')
    hcm['package'] = hcm['Package'].apply(calculate_total_lessons)
    hcm = hcm[['Phone', 'UID', 'Pay Time', 'Real Pay(VND)', 'Payment Method', 'package', 'Type', 'Sales']]
    hcm['UID'] = hcm['UID'].astype(str).str.replace('.0', '', regex=False)

    hn = _read_excel_robust(latest["revenue_hn"], 'INCOME')
    hn.columns = hn.columns.str.strip()
    hn = hn[['Phone', 'UID', 'Pay Time', 'Real Pay(VND)', 'Payment Method', '总 B (被推荐） 课数', 'Type', 'Sales']]
    hn['Pay Time'] = pd.to_datetime(hn['Pay Time'], errors='coerce')
    hn = hn.rename(columns={'总 B (被推荐） 课数': 'package'})
    hn['package'] = pd.to_numeric(hn['package'], errors='coerce').astype('Int64')

    dn = _read_excel_robust(latest["revenue_dn"], 'REVENUE')
    dn.columns = dn.columns.str.strip()
    dn['package'] = dn['Package'].apply(calculate_total_lessons)
    dn['UID'] = dn['UID'].astype(str).str.replace('.0', '', regex=False)
    dn = dn[['Phone', 'UID', 'Pay Time', 'Real Pay(VND)', 'Payment Method', 'package', 'Type', 'Sales']]

    rev = pd.concat([dn, hcm, hn], ignore_index=True)
    rev['UID'] = pd.to_numeric(rev['UID'], errors='coerce').astype('Int64')
    rev = rev.sort_values(['UID', 'Pay Time'])
    rev = rev.rename(columns={'Payment Method': 'order_num_method', 'Sales': 'Sale_pay'})
    rev['Sale_pay'] = rev['Sale_pay'].fillna('').astype(str).apply(lambda x: unidecode(x).title())
    rev['UID'] = _clean_uid_13(rev['UID'])
    rev['Type'] = rev['Type'].map(SOURCE_MAP).fillna(rev['Type'])
    return rev


def load_remaining_lesson(latest):
    rl = _read_excel_robust(latest["remaining_lesson"])
    rl['Order Price VND'] = rl['Order Price VND'].astype(str).str.replace('.', '', regex=False) + '0'
    rl['Order ID'] = rl['Order ID'].astype(str)
    rl = rl[~rl['UID'].isin([3174442996, 3298336217])]
    rl = rl[~rl['Order ID'].isin(['726418402842882.0'])]
    rl['Purchase Time'] = pd.to_datetime(rl['Purchase Time'], errors='coerce')
    rl['Last class time'] = pd.to_datetime(rl['Last class time'], errors='coerce')
    uid = rl['UID'].astype(str).str.replace('.0', '', regex=False).str.strip()
    rl['UID'] = uid.apply(lambda x: x[1:] if (len(x) == 11 and x.startswith('3')) else x)
    rl['UID'] = pd.to_numeric(rl['UID'], errors='coerce').astype('Int64')
    return rl
