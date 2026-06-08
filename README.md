# DA-OD1RP — Dashboard Retention / Gia hạn (standalone)

Pipeline **độc lập**, chạy local từ file thô → sinh `outputs/dashboard_data.csv` → Streamlit.
**Không** dùng database `palfish`, **không** dùng Google Sheet khi chạy, **không** ảnh hưởng DA1RP / Power BI.

## Chạy local
```bash
pip install -r requirements.txt
python run_etl.py            # đầy đủ (có tốc độ học thực tế; đọc file 77MB ~1-2 phút)
python run_etl.py --no-pace  # nhanh, bỏ pace
streamlit run app.py         # mở dashboard
```

## Dashboard
- **Tab 1 — Tổng tất cả đơn hàng**; **Tab 2 — OD1 → OD2** (lọc `vc_order_num == 1`).
- Bộ lọc: khoảng tháng theo `end_date`, team, tùy chọn loại Expired/On-hold.
- Chart: số khách đến hạn (cột) + tỷ lệ chuyển đổi/gia hạn % (đường) theo tháng.
- Bảng chi tiết (tải CSV).

## Dữ liệu đầu vào (đặt trong thư mục `Input` — KHÔNG commit lên GitHub)
revenue HCM/HN/DN, `remaining_lesson__vn__*`, `国际化用户课程状态明细表_越南*`, leads.
`dim_sale.csv` + `dim_channel.csv` đã kèm trong repo (refresh bằng `python fetch_dims.py`).

## Kiến trúc
`config.py` (tìm file, không DB) → `etl/ingest.py` → `etl/due_date.py` (end_date + value_chain + status,
đóng băng đơn đã hết bằng `state/snapshot_prev.csv` thay snapshot DB) → `etl/dims.py` (team) →
`etl/source.py` (nguồn) → `etl/pace.py` (tốc độ học) → `run_etl.py` xuất `outputs/dashboard_data.csv`.

## Cập nhật hằng ngày
```bash
python run_etl.py            # sinh lại outputs/dashboard_data.csv
git add outputs/dashboard_data.csv dim_sale.csv dim_channel.csv
git commit -m "data: refresh $(date +%F)"
git push                      # Streamlit Cloud tự deploy lại
```

> ⚠️ Repo phải để **Private** (dữ liệu có UID khách). File thô & `outputs/orders_full.csv` đã được `.gitignore`.
