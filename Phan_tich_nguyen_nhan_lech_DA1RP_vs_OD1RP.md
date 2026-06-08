# Vì sao DA1RP và OD1RP lệch số "khách đến hạn"?
*(Ví dụ: HCM, tháng 6/2026 — DA1RP = 79, OD1RP = 92)*

## Kết luận nhanh

Con số không sai vì lỗi tính toán. **Hai báo cáo đang đếm hai thứ khác nhau**, nên việc OD1RP (phạm vi hẹp hơn) ra số cao hơn DA1RP (phạm vi rộng hơn) là hoàn toàn có thể xảy ra.

Hiểu lầm cốt lõi: *"rộng hơn" (tính tất cả lần mua) ≠ "nhiều khách đến hạn hơn trong 1 tháng".* Một báo cáo "khách đến hạn tháng X" xếp **mỗi khách vào đúng 1 tháng**. Vấn đề là hai dự án **neo (anchor) khách vào đơn hàng khác nhau**:

- **DA1RP** neo khách vào **đơn MỚI NHẤT / đang active** (vòng mua hiện tại), tính lại mỗi ngày.
- **OD1RP** neo khách vào **Order 1**, và tháng đáo hạn bị **"đóng băng"** trong file Master.

Vì neo khác nhau, hai tập khách của cùng một tháng **không phải quan hệ tập con** — chúng lệch nhau, và OD1RP gom thêm những khách mà DA1RP đã xếp sang tháng khác hoặc đã loại.

---

## Con số kiểm chứng (HCM, 2026-06)

| Cách đếm | Số khách |
|---|---|
| OD1RP — `Hist_UID_Order1_Contractual`, neo Order-1 | **92** (khớp với "hơn 90") |
| DA1RP — khách có đơn active đáo hạn trong tháng | **79** |

Bóc tách 92 khách của OD1RP (chạy lại bằng `compare_da1rp_vs_od1rp.py`):

| Nhóm | Số khách | DA1RP có đếm vào T6 không? |
|---|---|---|
| Còn active, Order 1 cũng là đơn mới nhất | **43** | Có (phần lõi chung của cả 2) |
| Đã học hết, remain ≤ 0 | **42** | Không — DA1RP đánh `Expired`, gắn về tháng hết thật |
| Đã gia hạn lên OD2+ | **7** | Không — DA1RP neo vào OD2 (đáo hạn T7, T11, T12, 2027) |

→ Chính 42 + 7 khách "thừa" này khiến OD1RP = 92 > DA1RP = 79, **dù OD1RP hẹp hơn về phạm vi.**

---

## Các nguyên nhân gốc (xếp theo mức tác động)

### 1. Neo vào đơn khác nhau (nguyên nhân chính)
- DA1RP: `account_status = 'Active'`, dùng `end_date_N` của **đơn cao nhất (max order)** → mỗi khách 1 dòng theo vòng mua **hiện tại**.
- OD1RP: chỉ tính dòng `order_number_of_value_chain == 1` → neo theo **Order 1**.
- Hệ quả: khách đã gia hạn OD2 thì DA1RP xếp theo tháng OD2, còn OD1RP vẫn để ở tháng OD1. Hai tập không lồng nhau.

### 2. Tháng đáo hạn bị "đóng băng" trong OD1RP
- OD1RP có **file Master** (`Step4.2_Master_Expected_Date.csv`) lưu vết `expected_runout_date` lần đầu nhìn thấy và **không cập nhật lại** kể cả khi học viên đã học xong.
- Kiểm chứng: **88/92** khách lấy `Final_Reporting_Month` từ Master (đóng băng), chỉ 4 lấy từ `contractual_end_date`.
- DA1RP thì **tính lại mỗi ngày** từ snapshot hôm qua; đơn đã hết buổi (remain = 0) bị snap `end_date_N` về ngày hết thật (quá khứ) → rơi khỏi tháng 6.

### 3. Bộ lọc trạng thái khác nhau
- OD1RP chỉ loại `Frozen` / `On-hold`, **vẫn đếm cả khách đã học hết (Expired)**.
- DA1RP coi remain ≤ 0 là `Expired` và **loại khỏi danh sách "đến hạn cần chăm"**.
- Đây là lý do 42 khách remain ≤ 0 vẫn nằm trong 92 của OD1RP.

### 4. Công thức tính duration khác nhau (tác động phụ trong ca này)
- DA1RP **cứng 2 buổi/tuần**: `duration = (TotalLesson // 2) * 7 + (TotalLesson % 2) * 3.5` ngày.
- OD1RP **đọc tần suất gói** (`fixed_non_fixed`, vd 2/W, 3/W, x/M): `duration = lessons / freq * 7` (tuần) hoặc `* 30` (tháng).
- Với HCM/T6, 91/92 đơn là gói 2/W nên hai công thức gần như trùng → ảnh hưởng nhỏ **ở ca này**. Nhưng với gói 3/W, 4/W, x/M thì ngày đáo hạn (và do đó THÁNG) sẽ lệch — gây sai khác ở team/tháng khác.

### 5. Khác tập dữ liệu & mapping team
- OD1RP chạy trên dữ liệu **GMV × REM đã match** (matching/scoring riêng) + mapping team bằng `Sale_member_Info.csv`.
- DA1RP chạy trên `remaining_lesson` + `leads` join với `dim_sale` (cột `Cơ sở`).
- Hai tập khách và cách gán team **không trùng khít 100%**, tạo thêm chênh lệch nền.

---

## Vậy con số nào "đúng"?

Tùy mục đích sử dụng:

- Nếu cần **danh sách khách cần gọi gia hạn NGAY trong tháng** → logic DA1RP (neo đơn đang active) hợp lý hơn. OD1RP đang **cộng dồn** cả khách đã học xong và khách đã gia hạn rồi, nên số bị thổi lên.
- Nếu cần **phân tích cohort OD1→OD2** (bao nhiêu Order 1 đáo hạn trong tháng và tỷ lệ chuyển lên OD2) → OD1RP đúng mục tiêu, nhưng **không nên** so trực tiếp với "khách đến hạn" của DA1RP.

---

## Khuyến nghị để 2 bên khớp logic "khách đến hạn cần chăm"

1. **Loại khách đã mua OD2** (`Hist_Order1_UID_Bought2Ever`) khỏi danh sách "OD1 đến hạn cần chăm" — họ đã gia hạn, không còn là đối tượng cần chăm.
2. **Xử lý đơn đã hết buổi (remain ≤ 0):** không giữ tháng đóng băng; hoặc loại khỏi danh sách "đến hạn", hoặc gắn về tháng hết thật như DA1RP.
3. **Bỏ đóng băng tháng khi học viên đã học xong** — chỉ nên giữ vết Master cho đơn còn đang học (remain > 0).
4. **Đồng bộ công thức duration:** dùng đúng tần suất gói ở cả hai (hoặc cùng cứng 2/W) để ngày đáo hạn nhất quán.
5. **Thống nhất định nghĩa "đến hạn" và mapping team** giữa hai dự án trước khi đối chiếu số.

---

## File kèm trong thư mục này
- `compare_da1rp_vs_od1rp.py` — script tái hiện & bóc tách (chạy lại được trên máy bạn).
- `HCM_2026-06_audit.csv` — danh sách 92 khách OD1RP kèm phân loại lý do lệch.
