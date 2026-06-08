# Dashboard Retention / Gia hạn (Streamlit)

## Chạy nhanh
```bash
pip install -r requirements.txt
streamlit run app.py
```
Mở trình duyệt ở địa chỉ Streamlit in ra (mặc định http://localhost:8501).

## Cấu trúc
- `prepare_dashboard_data.py` — chuẩn hoá dữ liệu đơn hàng về `dashboard_data.csv`.
  - Tự ưu tiên `remaining_lesson_with_vc.csv` (export DA1RP đã có value-chain) nếu có;
    nếu không, dùng `Order 1 - Order 2/Output/GMV_x_REM_end_date.csv`.
- `app.py` — dashboard Streamlit, đọc `dashboard_data.csv`.

## Tính năng
- 2 tab: **Tổng tất cả đơn hàng** và **OD1 → OD2** (lọc `vc_order_num == 1`).
- Bộ lọc **khoảng tháng theo end_date** + **team** + tùy chọn loại Expired/On-hold.
- Chart: **số khách đến hạn** (cột) & **tỷ lệ chuyển đổi/gia hạn %** (đường) theo tháng.
- Bảng tổng hợp theo tháng + **bảng chi tiết** (tải CSV).

## Định nghĩa
- **end_date**: ngày đáo hạn dự kiến (đơn đang dùng chạy hết buổi).
- **renewed / đã gia hạn**: khách đã mua đơn kế tiếp trong cùng value chain.
  Tab OD1→OD2: đã mua Order 2.
- **Lưu ý**: tháng hiện tại/tương lai có tỷ lệ chuyển đổi thấp vì khách chưa kịp gia hạn.

## Cập nhật dữ liệu hằng ngày
1. Chạy DA1RP để sinh bảng đơn (kèm `value_chain`, `vc_order_num`).
2. Export ra `remaining_lesson_with_vc.csv` (đặt cạnh các script này).
3. `python prepare_dashboard_data.py` → cập nhật `dashboard_data.csv`.
4. Reload dashboard.
