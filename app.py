# -*- coding: utf-8 -*-
"""
Dashboard Retention / Gia han  (Streamlit)
- Tab 1: Tong tat ca don hang (moi vong mua)
- Tab 2: Rieng OD1 -> OD2 (don dau tien cua value chain)
- Bo loc theo thang cua end_date (+ team)
- Chart: so luong khach den han & ty le chuyen doi (gia han) theo thang
- Bang chi tiet + tai xuong

Chay:  streamlit run app.py
Du lieu: dashboard_data.csv (tao boi prepare_dashboard_data.py)
"""
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Retention / Gia han Dashboard", layout="wide")

HERE = Path(__file__).resolve().parent
DATA = HERE / "outputs" / "dashboard_data.csv"
if not DATA.exists():
    DATA = HERE / "dashboard_data.csv"


@st.cache_data(show_spinner=False)
def load_data(path):
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    df["vc_order_num"] = pd.to_numeric(df["vc_order_num"], errors="coerce")
    df["real_money"] = pd.to_numeric(df["real_money"], errors="coerce").fillna(0)
    df["days_to_renew"] = pd.to_numeric(df["days_to_renew"], errors="coerce")
    df["renewed"] = df["renewed"].astype(str).str.lower().isin(["true", "1", "yes"])
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    for c in ["team", "sale", "teacher", "package", "status", "end_month",
              "next_pay_month", "renew_timing", "value_chain"]:
        if c in df:
            df[c] = df[c].fillna("")
    return df


def agg_by_month(df):
    g = (df.dropna(subset=["end_date"])
           .groupby("end_month")
           .agg(khach_den_han=("uid", "nunique"),
                so_don=("uid", "size"),
                da_gia_han=("renewed", "sum"),
                doanh_thu=("real_money", "sum"))
           .reset_index()
           .sort_values("end_month"))
    g["ty_le_chuyen_doi_%"] = (g["da_gia_han"] / g["so_don"] * 100).round(1).fillna(0)
    return g


def combo_chart(g, title):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=g["end_month"], y=g["khach_den_han"],
                         name="Khách đến hạn", marker_color="#4C78A8"),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=g["end_month"], y=g["ty_le_chuyen_doi_%"],
                             name="Tỷ lệ chuyển đổi %", mode="lines+markers",
                             line=dict(color="#E45756", width=3)),
                  secondary_y=True)
    fig.update_layout(title=title, height=430, legend=dict(orientation="h", y=1.12),
                      margin=dict(t=70, b=40, l=10, r=10), hovermode="x unified")
    fig.update_yaxes(title_text="Số khách đến hạn", secondary_y=False)
    fig.update_yaxes(title_text="Tỷ lệ chuyển đổi (%)", range=[0, 100], secondary_y=True)
    fig.update_xaxes(type="category")  # luon hien nhan thang (vd 2026-06), tranh truc thoi gian loi
    return fig


def render_tab(df, key):
    if df.empty:
        st.warning("Không có dữ liệu sau khi lọc.")
        return
    g = agg_by_month(df)
    c1, c2, c3, c4 = st.columns(4)
    tot_due = int(df["uid"].nunique())
    tot_orders = int(len(df))
    tot_renew = int(df["renewed"].sum())
    conv = (tot_renew / tot_orders * 100) if tot_orders else 0
    c1.metric("Khách đến hạn (unique UID)", f"{tot_due:,}")
    c2.metric("Số đơn đến hạn", f"{tot_orders:,}")
    c3.metric("Đã gia hạn", f"{tot_renew:,}")
    c4.metric("Tỷ lệ chuyển đổi", f"{conv:.1f}%")

    st.plotly_chart(combo_chart(g, "Số khách đến hạn & tỷ lệ chuyển đổi theo tháng (end_date)"),
                    use_container_width=True, key=f"chart_{key}")

    st.caption("Lưu ý: tháng hiện tại / tương lai có tỷ lệ chuyển đổi thấp vì khách chưa kịp gia hạn.")

    with st.expander("Bảng tổng hợp theo tháng", expanded=False):
        st.dataframe(g, use_container_width=True, hide_index=True)

    st.subheader("Bảng chi tiết")
    # Hien thi cot giong file DA1RP
    colmap = [
        ("uid", "UID"), ("status_renew", "Status Renewal"), ("remain_lesson", "Remain lesson"),
        ("real_money", "GMV latest"), ("teacher", "Advisor"), ("sale", "Sale"),
        ("team", "Sale Team"), ("purchase_time", "Purchase Time"),
        ("end_date", "end_date_N"), ("order_num", "order_num"),
    ]
    cols = [(src, dst) for src, dst in colmap if src in df.columns]
    detail = df[[c for c, _ in cols]].rename(columns=dict(cols))
    for dc in ("Purchase Time", "end_date_N"):
        if dc in detail.columns:
            detail[dc] = pd.to_datetime(detail[dc], errors="coerce").dt.strftime("%Y-%m-%d")
    sort_cols = [c for c in ["Sale Team", "UID"] if c in detail.columns]
    if sort_cols:
        detail = detail.sort_values(sort_cols)
    st.dataframe(detail, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Tải bảng chi tiết (CSV)",
                       detail.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"chi_tiet_{key}.csv", mime="text/csv",
                       key=f"dl_{key}")


# ---------------- Load ----------------
st.title("📊 Dashboard Retention / Gia hạn")

if not DATA.exists():
    up = st.file_uploader("Chưa thấy dashboard_data.csv — tải lên file dữ liệu", type=["csv"])
    if up is None:
        st.stop()
    df_all = load_data(up)
else:
    df_all = load_data(DATA)

# ---------------- Filters ----------------
months = sorted([m for m in df_all["end_month"].dropna().unique() if m])
teams = sorted([t for t in df_all["team"].dropna().unique() if t])

st.sidebar.header("Bộ lọc")
if months:
    # mac dinh: cua so quanh thang hien tai
    now = pd.Timestamp.now().strftime("%Y-%m")
    default_start = next((m for m in months if m >= (pd.Timestamp.now() - pd.DateOffset(months=6)).strftime("%Y-%m")), months[0])
    default_end = next((m for m in reversed(months) if m <= (pd.Timestamp.now() + pd.DateOffset(months=6)).strftime("%Y-%m")), months[-1])
    m_start, m_end = st.sidebar.select_slider(
        "Khoảng tháng (end_date)", options=months,
        value=(default_start, default_end))
else:
    m_start, m_end = None, None

sel_teams = st.sidebar.multiselect("Team", teams, default=teams)
exclude_expired = st.sidebar.checkbox("Chỉ khách còn active (loại Expired/On hold)", value=False)

mask = pd.Series(True, index=df_all.index)
if m_start:
    mask &= df_all["end_month"].between(m_start, m_end)
if sel_teams:
    mask &= df_all["team"].isin(sel_teams)
if exclude_expired:
    mask &= ~df_all["status"].str.lower().isin(["expired", "on-hold", "on hold"])
df_f = df_all[mask].copy()

st.caption(f"Đang lọc: {m_start} → {m_end} | {len(sel_teams)} team | {len(df_f):,} đơn")

tab1, tab2 = st.tabs(["🧾 Tổng tất cả đơn hàng", "1️⃣➡️2️⃣ OD1 → OD2"])
with tab1:
    render_tab(df_f, "all")
with tab2:
    od1 = df_f[df_f["vc_order_num"] == 1].copy()
    st.caption("Chỉ tính Order 1 của mỗi value chain (đơn đầu mỗi chu kỳ học). 'Đã gia hạn' = đã mua Order 2 cùng chuỗi.")
    render_tab(od1, "od1")
