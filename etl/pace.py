# -*- coding: utf-8 -*-
"""Stage 7: toc do hoc thuc te tu 课程状态明细表 (streaming, doc file 77MB nhe RAM).
Dem so buoi 'da hoc' (课程状态 == 已完课) trong WINDOW_WEEKS tuan gan nhat -> buoi/tuan/UID.
"""
import re, zipfile
from xml.etree import ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
WINDOW_WEEKS = 8
COMPLETED = "已完课"
# chi so cot (0-based) trong 课程状态明细表
C_OPEN, C_LESSONID, C_UID, C_STATUS = 0, 5, 7, 27


def _col(ref):
    s = re.match(r"([A-Z]+)\d+", ref).group(1)
    n = 0
    for ch in s:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def compute_pace(xlsx_path, today=None):
    """Tra ve DataFrame: UID, lessons_done_8w, lessons_per_week_real."""
    today = pd.Timestamp(today or pd.Timestamp.now().normalize())
    cutoff = today - timedelta(weeks=WINDOW_WEEKS)
    z = zipfile.ZipFile(xlsx_path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.findall(f"{NS}si"):
            shared.append("".join(t.text or "" for t in si.iter(f"{NS}t")))
    sheet = [n for n in z.namelist() if n.startswith("xl/worksheets/sheet")][0]
    from collections import defaultdict
    done = defaultdict(set)  # uid -> set(lesson_id) da hoc trong window
    first = True
    for _, el in ET.iterparse(z.open(sheet), events=("end",)):
        if el.tag != f"{NS}row":
            continue
        if first:  # bo header
            first = False; el.clear(); continue
        cells = {}
        for c in el.findall(f"{NS}c"):
            ref = c.get("r")
            if not ref:
                continue
            ci = _col(ref)
            v = c.find(f"{NS}v")
            if v is not None and v.text is not None:
                cells[ci] = shared[int(v.text)] if c.get("t") == "s" else v.text
            else:
                isn = c.find(f"{NS}is")  # inline string
                if isn is not None:
                    cells[ci] = "".join(t.text or "" for t in isn.iter(f"{NS}t"))
        el.clear()
        if cells.get(C_STATUS) != COMPLETED:
            continue
        op = cells.get(C_OPEN)
        try:
            d = pd.to_datetime(op, errors="coerce")
        except Exception:
            d = None
        if d is None or pd.isna(d) or d < cutoff or d > today:
            continue
        uid = cells.get(C_UID)
        if uid is None:
            continue
        uid = re.sub(r"\.0$", "", str(uid)).strip()
        lid = cells.get(C_LESSONID) or f"{op}"
        done[uid].add(str(lid))
    rows = [(u, len(s), round(len(s) / WINDOW_WEEKS, 2)) for u, s in done.items()]
    df = pd.DataFrame(rows, columns=["UID", "lessons_done_8w", "lessons_per_week_real"])
    df["UID"] = pd.to_numeric(df["UID"], errors="coerce").astype("Int64")
    return df
