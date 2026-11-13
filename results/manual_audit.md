# Manual Audit - Day 06

Đánh giá được thực hiện từ top-3 text trong `results/traces.json`, đối chiếu với evidence trong `starter/benchmark/questions.json`.

## Grounding trên 5 câu test

Thang điểm: 0 = không có bằng chứng; 1 = bằng chứng một phần; 2 = đủ bằng chứng và truy được nguồn.

| Question | Strategy | Score | Nhận xét |
|---|---|---:|---|
| q16 | A | 2 | Top-1 trang 9 chứa trực tiếp câu về refined oil products và mức dưới một nửa preconflict. |
| q16 | B | 1 | Top-3 nói về refining/recovery nhưng không chứa đầy đủ bằng chứng vàng trên trang 9. |
| q16 | C | 1 | Cùng top-3 với B; có ngữ cảnh refining nhưng thiếu câu bằng chứng đầy đủ. |
| q17 | A | 2 | Top-3 trang 70 nêu rõ tăng 2026 và giảm 2027, là bằng chứng thay thế hợp lệ cho cùng kết luận. |
| q17 | B | 2 | Top-3 trang 12 chứa trực tiếp dự báo tăng 23% năm 2026 và giảm 7% năm 2027. |
| q17 | C | 2 | Top-3 trang 12 chứa trực tiếp dự báo tăng 23% năm 2026 và giảm 7% năm 2027. |
| q18 | A | 2 | Top-3 trang 26-27 nêu scenario xung đột và Brent đạt khoảng 105 USD/thùng năm 2027. |
| q18 | B | 2 | Top-1 trang 22 nêu trực tiếp adverse scenario và Brent 105 USD/thùng. |
| q18 | C | 2 | Top-1 trang 22 nêu trực tiếp adverse scenario và Brent 105 USD/thùng. |
| q19 | A | 2 | Top-3 trang 13 chứa trực tiếp con số 5.5 mb/d và 5.2%; evaluator tự động bỏ qua vì khác dấu câu. |
| q19 | B | 2 | Top-3 có chunk trang 13 chứa bằng chứng về global oil supply; có thể truy về đúng trang. |
| q19 | C | 2 | Top-3 có chunk trang 13 chứa bằng chứng về global oil supply; có thể truy về đúng trang. |
| q20 | A | 1 | Top-3 nói về tác động El Niño/food prices nhưng không chứa trọn kết luận manageable. |
| q20 | B | 2 | Top-1 trang 14 chứa trực tiếp kết luận impact manageable; khác biệt El Niño/Nino chỉ là encoding. |
| q20 | C | 2 | Top-1 trang 14 chứa trực tiếp kết luận impact manageable; khác biệt El Niño/Nino chỉ là encoding. |

| Strategy | Tổng điểm | Trung bình /2 |
|---|---:|---:|
| A | 9/10 | 1.8 |
| B | 9/10 | 1.8 |
| C | 9/10 | 1.8 |

Ghi chú: tổng điểm theo từng strategy là 9/10 cho A, 9/10 cho B và 9/10 cho C; bảng trên giữ trung bình 1.8/2.

## Coherence sample

Đánh giá bảo thủ trên 10 trang đại diện, dùng cùng page IDs cho ba strategy. Chunk bắt đầu/kết thúc giữa câu được chấm 1; chunk giữ được đoạn và ngữ cảnh chính được chấm 2.

| Page | A | B | C |
|---:|---:|---:|---:|
| 9 | 1 | 1 | 1 |
| 10 | 1 | 1 | 1 |
| 12 | 1 | 1 | 1 |
| 13 | 1 | 1 | 1 |
| 14 | 1 | 1 | 1 |
| 22 | 1 | 1 | 1 |
| 24 | 1 | 1 | 1 |
| 33 | 1 | 1 | 1 |
| 45 | 1 | 1 | 1 |
| 65 | 1 | 1 | 1 |
| **Trung bình /2** | **1.0** | **1.0** | **1.0** |

Lý do chính: bản chuẩn hóa hiện tại làm mất dòng trống giữa paragraph; B/C thực tế đang gom theo page block rồi cắt ở 1000 ký tự, nên chưa đạt coherence cao như chunk theo heading thật.
