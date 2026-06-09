# DA-OD1RP — Dashboard Retention / Gia hạn (đồng nhất 100% với DA1RP)

DA-OD1RP đọc **thẳng** file export `remaining_lesson3` của DA1RP (cùng universe + end_date + status + team),
và **chỉ tính thêm** `value_chain` / `vc_order_num` để có view **OD1 → OD2**. Vì dùng chung nguồn nên
số liệu **giống DA1RP 100%**. Không đụng DB của DA1RP (chỉ đọc file CSV export).

## Quy trình hằng ngày
1. Trong SSMS, **bật "Include column headers"** rồi export:
   ```sql
   SELECT uid, order_id, end_date_n, remain_lesson_number, status_renew,
          teacher, sale, depart7_name_sale, order_price_vnd, purchase_time,
          order_num, type_lesson, payment_number_n_1
   FROM remaining_lesson3
   ```
   Lưu (ghi đè) thành `da1rp_remaining_lesson3.csv` trong thư mục này.
2. Chạy:
   ```bash
   python build_dashboard.py
   git add outputs/dashboard_data.csv ; git commit -m "data refresh" ; git push
   ```
3. Streamlit Cloud tự deploy lại (`app.py`).

## Dashboard (app.py)
- 2 tab: **Tổng tất cả đơn hàng** & **OD1 → OD2** (lọc `vc_order_num == 1`).
- Card: Khách đến hạn / Số đơn / Đã gia hạn / Tỷ lệ + breakdown **Early / On-time / Late / Tổng gia hạn**.
- Bộ lọc: **Từ tháng → Đến tháng** (theo end_date) + team.
- Bảng chi tiết: đúng cột DA1RP (UID, Status Renewal, Remain lesson, GMV latest, Advisor, Sale, Sale Team, Purchase Time, end_date_N, order_num).

## Cột tối thiểu bắt buộc trong export
`uid, order_id, end_date_n, status_renew, depart7_name_sale` (các cột còn lại nên có để hiển thị đầy đủ).
Nếu export **không có header**, đặt đúng thứ tự cột như câu SQL trên.

## File phụ (chế độ tính độc lập — không bắt buộc)
`run_etl.py` + `etl/` là bản tự tính từ file thô (revenue + remaining_lesson + pace). Khớp ~97-99%
nhưng không đảm bảo 100% do khác universe. Mặc định nên dùng `build_dashboard.py`.
