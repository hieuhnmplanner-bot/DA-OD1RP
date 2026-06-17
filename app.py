# -*- coding: utf-8 -*-
"""Dashboard Retention / Gia han (Streamlit) - doc tu outputs/dashboard_data.csv.
2 tab (Tong / OD1->OD2), bo loc thang+team, card 1 hang, chon ngon ngu VI/EN/ZH."""
from pathlib import Path
import re
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Retention / Renewal Dashboard", layout="wide")

HERE = Path(__file__).resolve().parent
DATA = HERE / "outputs" / "dashboard_data.csv"
if not DATA.exists():
    DATA = HERE / "dashboard_data.csv"

RENEWAL = ["Early Renewal", "On-time Renewal", "Late Renewal"]
# "Return after End_date 90 days" = chu ky moi -> KHONG tinh gia han o BAT KY chi so nao
# (CRR, RRR, Upsell, Renewal Revenue deu chi dung RENEWAL: Early/On-time/Late)

# ---------------- i18n ----------------
LANG = {
    "Tiếng Việt": {
        "title": "📊 Dashboard Retention / Gia hạn",
        "filters": "Bộ lọc", "language": "Ngôn ngữ",
        "from_month": "Từ tháng", "to_month": "Đến tháng", "team": "Team",
        "sale_f": "Sale", "advisor_f": "Advisor (GVCN)", "uid_f": "UID (gõ số, cách nhau dấu phẩy)", "all_hint": "Để trống = tất cả", "all_short": "Tất cả",
        "tab_group": "📊 Theo nhóm", "by_team": "Theo Team", "by_sale": "Theo Sale", "by_advisor": "Theo Advisor",
        "groups_title": "📊 Thống kê theo nhóm (Team / Sale / Advisor)",
        "metric_pick": "Chỉ số xem", "n_sel": "{n} đã chọn",
        "active_only": "Chỉ khách còn active (loại Expired/On hold)",
        "filtering": "Đang lọc: {a} → {b} | {n} team | {o:,} đơn",
        "tab_all": "🧾 Tổng tất cả đơn hàng", "tab_od1": "1️⃣➡️2️⃣ OD1 → OD2",
        "tab2_cap": "Chỉ tính Order 1 của mỗi value chain (đơn đầu mỗi chu kỳ). 'Đã gia hạn' = đã mua Order 2 cùng chuỗi.",
        "due": "Khách đến hạn (UID)", "revenue": "Renewal Revenue",
        "crr": "CRR – Tỷ lệ gia hạn KH", "crr_h": "Số khách gia hạn / Số khách hết hạn trong kỳ",
        "rrr": "RRR – Tỷ lệ gia hạn DT", "rrr_h": "Doanh thu gia hạn / Tổng giá trị gói hết hạn trong kỳ",
        "upsell": "Upsell – Nâng giá trị", "upsell_h": "Giá trị đơn gia hạn mới / Giá trị đơn cũ (của nhóm đã gia hạn). >100% = khách chi nhiều hơn lần trước",
        "rev_h": "Tổng doanh thu các đơn gia hạn (đơn kế tiếp)",
        "early": "🟢 Early Renewal", "ontime": "🔵 On-time Renewal", "late": "🟡 Late Renewal",
        "total": "Σ Tổng đã gia hạn",
        "chart_title": "Số khách đến hạn & tỷ lệ chuyển đổi theo tháng (end_date)",
        "leg_due": "Khách đến hạn", "leg_conv": "Tỷ lệ chuyển đổi %",
        "y_due": "Số khách đến hạn", "y_conv": "Tỷ lệ chuyển đổi (%)",
        "cap": "Lưu ý: tháng hiện tại / tương lai có tỷ lệ chuyển đổi thấp vì khách chưa kịp gia hạn.",
        "monthly": "Bảng tổng hợp theo tháng", "detail": "Bảng chi tiết",
        "download": "⬇️ Tải bảng chi tiết (CSV)", "no_data": "Không có dữ liệu sau khi lọc.",
    },
    "English": {
        "title": "📊 Retention / Renewal Dashboard",
        "filters": "Filters", "language": "Language",
        "from_month": "From month", "to_month": "To month", "team": "Team",
        "sale_f": "Sale", "advisor_f": "Advisor", "uid_f": "UID (type number, comma-separated)", "all_hint": "Empty = all", "all_short": "All",
        "tab_group": "📊 By group", "by_team": "By Team", "by_sale": "By Sale", "by_advisor": "By Advisor",
        "groups_title": "📊 Breakdown by group (Team / Sale / Advisor)",
        "metric_pick": "Metric", "n_sel": "{n} selected",
        "active_only": "Active only (exclude Expired/On hold)",
        "filtering": "Filter: {a} → {b} | {n} teams | {o:,} orders",
        "tab_all": "🧾 All orders", "tab_od1": "1️⃣➡️2️⃣ OD1 → OD2",
        "tab2_cap": "Only Order 1 of each value chain. 'Renewed' = bought Order 2 in the same chain.",
        "due": "Customers Due (UID)", "revenue": "Renewal Revenue",
        "crr": "CRR – Customer Renewal", "crr_h": "Renewed customers / Customers due in period",
        "rrr": "RRR – Revenue Renewal", "rrr_h": "Renewal revenue / Total value of expiring packages",
        "upsell": "Upsell – Value Uplift", "upsell_h": "New renewal value / Old order value (of renewers). >100% = spending more than before",
        "rev_h": "Total revenue of renewal (next) orders",
        "early": "🟢 Early Renewal", "ontime": "🔵 On-time Renewal", "late": "🟡 Late Renewal",
        "total": "Σ Total Renewed",
        "chart_title": "Customers due & retention rate by month (end_date)",
        "leg_due": "Customers due", "leg_conv": "Retention rate %",
        "y_due": "Customers due", "y_conv": "Retention rate (%)",
        "cap": "Note: current/future months show low retention because customers haven't renewed yet.",
        "monthly": "Monthly summary", "detail": "Detail table",
        "download": "⬇️ Download detail (CSV)", "no_data": "No data after filtering.",
    },
    "中文": {
        "title": "📊 续费留存看板",
        "filters": "筛选", "language": "语言",
        "from_month": "起始月", "to_month": "结束月", "team": "团队",
        "sale_f": "销售", "advisor_f": "班主任", "uid_f": "UID (输入数字，逗号分隔)", "all_hint": "留空 = 全部", "all_short": "全部",
        "tab_group": "📊 按分组", "by_team": "按团队", "by_sale": "按销售", "by_advisor": "按班主任",
        "groups_title": "📊 分组统计 (团队 / 销售 / 班主任)",
        "metric_pick": "指标", "n_sel": "已选 {n}",
        "active_only": "仅在读学员（排除到期/暂停）",
        "filtering": "筛选: {a} → {b} | {n} 个团队 | {o:,} 单",
        "tab_all": "🧾 全部订单", "tab_od1": "1️⃣➡️2️⃣ OD1 → OD2",
        "tab2_cap": "仅统计每个学习周期的第 1 单。'已续费' = 同周期购买了第 2 单。",
        "due": "到期客户数 (UID)", "revenue": "续费金额",
        "crr": "CRR – 客户续费率", "crr_h": "续费客户数 / 当期到期客户数",
        "rrr": "RRR – 收入续费率", "rrr_h": "续费收入 / 当期到期套餐总价值",
        "upsell": "Upsell – 升单率", "upsell_h": "新续费金额 / 旧订单金额（仅续费客户）。>100% = 比上次花更多",
        "rev_h": "续费(下一单)订单的总收入",
        "early": "🟢 提前续费", "ontime": "🔵 准时续费", "late": "🟡 延迟续费",
        "total": "Σ 续费合计",
        "chart_title": "按月到期客户数与续费率 (end_date)",
        "leg_due": "到期客户", "leg_conv": "续费率 %",
        "y_due": "到期客户数", "y_conv": "续费率 (%)",
        "cap": "注意：当月/未来月份续费率偏低，因为客户尚未续费。",
        "monthly": "按月汇总表", "detail": "明细表",
        "download": "⬇️ 下载明细 (CSV)", "no_data": "筛选后无数据。",
    },
}


def _fmt_money(v, lang):
    v = float(v or 0)
    if lang == "中文":
        return f"{v/1e8:,.2f} 亿"      # 1 亿 = 10^8
    suffix = " tỷ" if lang == "Tiếng Việt" else " B"
    return f"{v/1e9:,.2f}{suffix}"     # 1 ty / 1 billion = 10^9


def _pct(v, lang=None):
    """64.3 -> '64,3%' (tieng Viet dung dau phay; EN/ZH dung dau cham)."""
    lang = lang or st.session_state.get("_lang", "Tiếng Việt")
    try:
        s = f"{float(v):.1f}%"
    except Exception:
        return ""
    return s.replace(".", ",") if lang == "Tiếng Việt" else s


@st.cache_data(show_spinner=False)
def load_data(path):
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    for col in ["vc_order_num", "real_money", "renewal_payment", "remain_lesson", "order_num"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "real_money" in df.columns:
        df["real_money"] = df["real_money"].fillna(0)
    if "renewed" in df.columns:
        df["renewed"] = df["renewed"].astype(str).str.lower().isin(["true", "1", "yes"])
    if "end_date" in df.columns:
        df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce", format="mixed")
    for c in ["team", "sale", "teacher", "package", "status", "end_month",
              "status_renew", "value_chain"]:
        if c in df:
            df[c] = df[c].fillna("")
    return df


def agg_by_month(df):
    _em = df["end_month"].astype(str)
    base = df[_em.str.len().eq(7) & _em.str.contains("-", regex=False)]
    due = base.groupby("end_month")["uid"].nunique()
    ren = base[base["status_renew"].isin(RENEWAL)].groupby("end_month")["uid"].nunique()
    g = pd.DataFrame({"due": due, "ren": ren}).fillna(0).astype(int).reset_index()
    g["conv"] = (g["ren"] / g["due"] * 100).round(1).fillna(0)
    return g.sort_values("end_month")


def combo_chart(g, t):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=g["end_month"], y=g["due"], name=t["leg_due"], marker_color="#4C78A8"),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=g["end_month"], y=g["conv"], name=t["leg_conv"],
                             mode="lines+markers", line=dict(color="#E45756", width=3)),
                  secondary_y=True)
    fig.update_layout(title=t["chart_title"], height=430, legend=dict(orientation="h", y=1.12),
                      margin=dict(t=70, b=40, l=10, r=10), hovermode="x unified")
    fig.update_yaxes(title_text=t["y_due"], secondary_y=False)
    fig.update_yaxes(title_text=t["y_conv"], range=[0, 100], secondary_y=True)
    fig.update_xaxes(type="category")
    return fig


def breakdown(df, col):
    """Thong ke theo nhom (col): due (UID het han), renewed, CRR, RRR, Upsell, revenue."""
    d = df.copy()
    d["_money"] = pd.to_numeric(d["real_money"], errors="coerce").fillna(0)
    rev_col = "renewal_payment" if "renewal_payment" in d.columns else "real_money"
    d["_new"] = pd.to_numeric(d[rev_col], errors="coerce").fillna(0)
    d = d[d[col].astype(str).str.len() > 0]
    if d.empty:
        return pd.DataFrame(columns=["name", "due", "crr", "rrr", "upsell", "revenue"])
    due = d.groupby(col)["uid"].nunique()
    stn = lambda v: d[d["status_renew"] == v].groupby(col)["uid"].nunique()
    renewed = stn("Early Renewal").add(stn("On-time Renewal"), fill_value=0).add(stn("Late Renewal"), fill_value=0)
    rev = d[d["status_renew"].isin(RENEWAL)]
    new_val = rev.groupby(col)["_new"].sum()
    old_val = rev.groupby(col)["_money"].sum()
    expiring = d.groupby(col)["_money"].sum()
    o = pd.DataFrame({"due": due})
    o["renewed"] = renewed.reindex(o.index).fillna(0)
    o["revenue"] = new_val.reindex(o.index).fillna(0)
    o["_old"] = old_val.reindex(o.index).fillna(0)
    o["_exp"] = expiring.reindex(o.index).fillna(0)
    o["crr"] = (o["renewed"] / o["due"] * 100).round(1)
    o["rrr"] = (o["revenue"] / o["_exp"].where(o["_exp"] > 0) * 100).round(1).fillna(0)
    o["upsell"] = (o["revenue"] / o["_old"].where(o["_old"] > 0) * 100).round(1).fillna(0)
    return o.reset_index().rename(columns={col: "name"})


def hbar(bdf, metric, label):
    lang = st.session_state.get("_lang", "Tiếng Việt")
    b = bdf.sort_values(metric, ascending=False).head(15).iloc[::-1]
    if metric == "revenue":
        txt = [_fmt_money(v, lang) for v in b[metric]]
    elif metric in ("crr", "rrr", "upsell"):
        txt = [f"{v:.1f}%" for v in b[metric]]
    else:
        txt = [f"{int(v):,}" for v in b[metric]]
    fig = go.Figure(go.Bar(x=b[metric], y=b["name"].astype(str), orientation="h",
                           text=txt, textposition="auto", marker_color="#4C78A8"))
    fig.update_layout(title=label, height=max(320, 26 * len(b) + 90),
                      margin=dict(t=50, b=20, l=10, r=10))
    return fig


def render_breakdown_tables(df, t):
    """Bang thong ke theo Team / Sale / Advisor — xem MOI chi so cung luc (due, CRR, RRR, Upsell, revenue)."""
    if df.empty:
        return
    lang = st.session_state.get("_lang", "Tiếng Việt")
    st.subheader(t["groups_title"])
    for col, lab, cap in [("team", t["by_team"], 0),
                          ("sale", t["by_sale"], 20),
                          ("teacher", t["by_advisor"], 20)]:
        if col not in df.columns:
            continue
        b = breakdown(df, col)
        if b.empty:
            continue
        b = b.sort_values("due", ascending=False)
        head = f"**{lab}**" + (f"  ·  top {cap}" if cap and len(b) > cap else "")
        if cap:
            b = b.head(cap)
        st.markdown(head)
        disp = pd.DataFrame({
            lab: b["name"].astype(str),
            t["due"]: b["due"].astype(int),
            t["total"]: b["renewed"].astype(int),
            "CRR": [_pct(v, lang) for v in b["crr"]],
            "RRR": [_pct(v, lang) for v in b["rrr"]],
            "Upsell": [_pct(v, lang) for v in b["upsell"]],
            t["revenue"]: [_fmt_money(v, lang) for v in b["revenue"]],
        })
        st.dataframe(disp, use_container_width=True, hide_index=True)


def render_tab(df, key, t):
    if df.empty:
        st.warning(t["no_data"])
        return
    sr = df["status_renew"] if "status_renew" in df.columns else pd.Series([], dtype=str)
    due = int(df["uid"].nunique())
    ne = int(df.loc[sr == "Early Renewal", "uid"].nunique())
    no = int(df.loc[sr == "On-time Renewal", "uid"].nunique())
    nl = int(df.loc[sr == "Late Renewal", "uid"].nunique())
    renewed = ne + no + nl
    crr = (renewed / due * 100) if due else 0
    rev_col = "renewal_payment" if "renewal_payment" in df.columns else "real_money"
    ren_mask = sr.isin(RENEWAL)
    money = pd.to_numeric(df["real_money"], errors="coerce").fillna(0)
    renew_new = pd.to_numeric(df.loc[ren_mask, rev_col], errors="coerce").fillna(0).sum()   # don gia han moi
    renew_old = money[ren_mask].sum()                                                       # don cu cua nhom gia han
    expiring_total = money.sum()                                                            # tong gia tri don het han
    rrr = (renew_new / expiring_total * 100) if expiring_total else 0
    upsell = (renew_new / renew_old * 100) if renew_old else 0

    # Hang 1: chi so chinh (ty le + doanh thu)
    a = st.columns(5)
    a[0].metric(t["due"], f"{due:,}")
    a[1].metric(t["crr"], _pct(crr), help=t["crr_h"])
    a[2].metric(t["rrr"], _pct(rrr), help=t["rrr_h"])
    a[3].metric(t["upsell"], _pct(upsell), help=t["upsell_h"])
    a[4].metric(t["revenue"], _fmt_money(renew_new, st.session_state.get("_lang", "Tiếng Việt")),
                help=f'{renew_new:,.0f}  •  {t["rev_h"]}')
    # Hang 2: so luong gia han theo loai
    b = st.columns(4)
    b[0].metric(t["early"], f"{ne:,}")
    b[1].metric(t["ontime"], f"{no:,}")
    b[2].metric(t["late"], f"{nl:,}")
    b[3].metric(t["total"], f"{renewed:,}")

    g = agg_by_month(df)
    st.plotly_chart(combo_chart(g, t), use_container_width=True, key=f"chart_{key}")
    st.caption(t["cap"])

    with st.expander(t["monthly"], expanded=False):
        gv = g.copy()
        gv["conv"] = [_pct(v) for v in gv["conv"]]
        gv = gv.rename(columns={"end_month": "month", "due": t["leg_due"],
                                "ren": t["total"], "conv": t["leg_conv"]})
        st.dataframe(gv, use_container_width=True, hide_index=True)

    render_breakdown_tables(df, t)

    st.subheader(t["detail"])
    # Don gia han CHUA kich hoat: hien "Not activated" o cot Status Renewal (type_lesson da gan o DA1RP)
    df = df.copy()
    if "status" in df.columns:
        _na = df["status"].astype(str).str.strip().str.lower() == "not activated"
        df.loc[_na, "status_renew"] = "Not activated"
    colmap = [("uid", "UID"), ("status_renew", "Status Renewal"), ("remain_lesson", "Remain lesson"),
              ("real_money", "GMV latest"), ("teacher", "Advisor"), ("sale", "Sale"),
              ("team", "Sale Team"), ("purchase_time", "Purchase Time"),
              ("end_date", "end_date_N"), ("order_num", "order_num"),
              ("value_chain", "value_chain"), ("vc_order_num", "value_chain_order_num")]
    cols = [(s, d) for s, d in colmap if s in df.columns]
    detail = df[[s for s, _ in cols]].rename(columns=dict(cols))
    for dc in ("Purchase Time", "end_date_N"):
        if dc in detail.columns:
            detail[dc] = pd.to_datetime(detail[dc], errors="coerce", format="mixed").dt.strftime("%Y-%m-%d")
    sort_cols = [x for x in ["Sale Team", "UID"] if x in detail.columns]
    if sort_cols:
        detail = detail.sort_values(sort_cols)
    st.dataframe(detail, use_container_width=True, hide_index=True)
    st.download_button(t["download"], detail.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"detail_{key}.csv", mime="text/csv", key=f"dl_{key}")


# ---------------- Load ----------------
if not DATA.exists():
    up = st.file_uploader("dashboard_data.csv?", type=["csv"])
    if up is None:
        st.stop()
    df_all = load_data(up)
else:
    df_all = load_data(DATA)

# Ngon ngu
lang = st.sidebar.selectbox("🌐 Language / 语言 / Ngôn ngữ", list(LANG.keys()), index=0)
st.session_state["_lang"] = lang
t = LANG[lang]

st.title(t["title"])
st.sidebar.header(t["filters"])

months = sorted([m for m in df_all["end_month"].dropna().unique() if m and len(str(m)) == 7])
teams = sorted([x for x in df_all["team"].dropna().unique() if x])

if months:
    ds = next((m for m in months if m >= (pd.Timestamp.now() - pd.DateOffset(months=6)).strftime("%Y-%m")), months[0])
    de = next((m for m in reversed(months) if m <= (pd.Timestamp.now() + pd.DateOffset(months=6)).strftime("%Y-%m")), months[-1])
    cfa, cfb = st.sidebar.columns(2)
    m_start = cfa.selectbox(t["from_month"], months, index=months.index(ds))
    m_end = cfb.selectbox(t["to_month"], months, index=months.index(de))
    if m_start > m_end:
        m_start, m_end = m_end, m_start
else:
    m_start, m_end = None, None

sales = sorted([x for x in df_all.get("sale", pd.Series(dtype=str)).dropna().unique() if x])
advisors = sorted([x for x in df_all.get("teacher", pd.Series(dtype=str)).dropna().unique() if x])

# Tat ca multiselect: DE TRONG = TAT CA (khong roi tag)
def _ms_popover(label, options, key):
    n = len(st.session_state.get(key, []))
    cap = t["all_short"] if n == 0 else t["n_sel"].format(n=n)
    with st.sidebar.popover(f"{label}: {cap}", use_container_width=True):
        return st.multiselect(label, options, default=[], key=key, placeholder=t["all_hint"])

sel_teams = _ms_popover(t["team"], teams, "ms_team")
sel_sales = _ms_popover(t["sale_f"], sales, "ms_sale")
sel_adv = _ms_popover(t["advisor_f"], advisors, "ms_adv")
uid_q = st.sidebar.text_input(t["uid_f"], value="")
exclude_expired = st.sidebar.checkbox(t["active_only"], value=False)

mask = pd.Series(True, index=df_all.index)
if m_start:
    mask &= df_all["end_month"].between(m_start, m_end)
if sel_teams:
    mask &= df_all["team"].isin(sel_teams)
if sel_sales:
    mask &= df_all["sale"].isin(sel_sales)
if sel_adv:
    mask &= df_all["teacher"].isin(sel_adv)
if uid_q.strip():
    toks = [x for x in re.split(r"[,\s]+", uid_q.strip()) if x]
    uids = df_all["uid"].astype(str)
    m_uid = pd.Series(False, index=df_all.index)
    for tk in toks:
        m_uid |= uids.str.contains(tk, regex=False)
    mask &= m_uid
if exclude_expired:
    mask &= ~df_all["status"].str.lower().isin(["expired", "on-hold", "on hold"])
df_f = df_all[mask].copy()

st.caption(t["filtering"].format(a=m_start, b=m_end, n=(len(sel_teams) or len(teams)), o=len(df_f)))

tab1, tab2 = st.tabs([t["tab_all"], t["tab_od1"]])
with tab1:
    render_tab(df_f, "all", t)
with tab2:
    od1 = df_f[df_f["vc_order_num"] == 1].copy()
    st.caption(t["tab2_cap"])
    render_tab(od1, "od1", t)
