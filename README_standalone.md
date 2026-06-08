# DA-OD1RP — Pipeline độc lập (không DB, không Google Sheet)

Mục tiêu: chạy local từ file thô → sinh file CSV → đẩy GitHub → Streamlit Cloud.
**Không** đụng database `palfish` và **không** đụng output/Power BI của DA1RP.

## Kiến trúc
```
File thô (Excel)  ──►  ETL local (pandas)  ──►  outputs/dashboard_data.csv  ──►  GitHub  ──►  Streamlit Cloud
   - revenue HCM/HN/DN          (không DB,
   - remaining_lesson            không gsheet)
   - 课程状态明细表 (pace)
   - leads (source)
   + dim_sale.csv (team)
   + state/snapshot_prev.csv (thay snapshot "hôm qua" của DB)
```

## 3 thứ thay thế để cắt lệ thuộc DA1RP
| DA1RP gốc | Bản standalone |
|---|---|
| `pd.read_sql(... conn)` lấy snapshot hôm qua từ DB | `state/snapshot_prev.csv` — tự đọc/ghi mỗi lần chạy |
| `client.open_by_key(...)` Google Sheet `dim_sale` | `dim_sale.csv` (export 1 lần, commit vào repo) |
| `insert_data_sql(...)`, `write_to_gsheet(...)` | ghi file CSV vào `outputs/` |

## Trạng thái build
- [x] **Stage 1 — Ingest** revenue 3 vùng + remaining_lesson (local). *Chạy thật OK.*
- [x] **Stage 2 — Team mapping** từ `dim_sale.csv` (theo `Cơ sở`, giống DA1RP). *96% coverage.*
- [x] **Stage 3 — Due date** `end_date_N` + đóng băng đơn đã hết bằng `state/snapshot_prev.csv` (thay DB).
- [x] **Stage 4 — Value chain** `value_chain` / `vc_order_num` (reset khi nghỉ > 90 ngày).
- [x] **Stage 5 — Status** `status_renew`, `type_lesson`, `account_status`.
- [x] **Stage 6 — Source** `source_type` từ revenue Type (UID + ngày gần nhất); `dim_channel.csv` sẵn sàng.
- [x] **Stage 7 — Pace** từ 课程状态明细表 (buổi 已完课/tuần). *Logic OK; file 77MB chạy ~1-2 phút trên máy bạn.*
- [x] **Stage 8 — Export** `outputs/dashboard_data.csv` + `outputs/orders_full.csv`.
- [x] **Dashboard** `app.py` đọc `outputs/dashboard_data.csv`.

## Cách chạy
```bash
pip install -r requirements.txt
python run_etl.py            # đầy đủ (có pace, đọc file 77MB ~1-2 phút)
python run_etl.py --no-pace  # nhanh, bỏ tốc độ học thực tế
streamlit run app.py         # mở dashboard
```

## ⚠️ Cần bạn cung cấp
1. **`dim_sale.csv`** — xuất từ Google Sheet `dim_sale`
   (`1mCDRdmfpxNyYrn0GoAPrTH6uOClWtI5SYB13cNDsHXM`, worksheet `dim_sale`)
   ra CSV, đặt tên `dim_sale.csv` cạnh các script. Xem cột mẫu ở `dim_sale.template.csv`.
   → Bắt buộc để map team (Stage 6). Không có nó thì team = UNKNOWN.
2. **Nguồn/kênh (Stage 8):** chốt dùng file leads sẵn có, hay cần thêm các sheet RE
   (`re_hcm`, `re_hn1`, `re_hn2`) — nếu cần thì export thêm ra CSV.

## Triển khai GitHub + Streamlit Cloud
1. Repo **PRIVATE** (dữ liệu có UID/SĐT khách).
2. `.gitignore` đã loại file thô nặng + state; chỉ commit code + `dashboard_data.csv` (đã bỏ cột phone).
3. Streamlit Community Cloud → trỏ repo → file `app.py`.
4. Hằng ngày: chạy `python run_etl.py` (local) → cập nhật `dashboard_data.csv` → `git push` → Cloud tự deploy.
   (Hoặc GitHub Action chạy theo lịch nếu để file thô ở nơi Action truy cập được.)
