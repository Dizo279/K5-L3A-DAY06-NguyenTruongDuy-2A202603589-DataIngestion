# Báo cáo cá nhân - Day 6

## Dữ liệu và pipeline

- **Chủ đề:** Commodity Markets Outlook - October 2026.
- **Nguồn:** Prospects Group, World Bank; `starter/data/raw/CMO-October-2026.pdf`.
- **Quy mô:** 70 trang vật lý, 68 trang có text; sử dụng khoảng trang vật lý 9-66 làm nội dung chính, tương ứng 58 trang sau khi loại bìa, trang trống, mục lục, references và back cover.
- **Quyền sử dụng:** PDF có trang copyright của World Bank; cần đối chiếu link/điều khoản chính thức trước khi nộp bài.
- **Chuẩn hóa:** `pypdf`, Unicode NFKC, chuẩn hóa khoảng trắng và giữ số trang vật lý; trang không có text vẫn được ghi nhận.
- **Embedding:** OpenRouter qua OpenAI-compatible API, model `openai/text-embedding-3-small`, 1536 chiều. API key đọc từ `.env`, không commit vào repo.
- **Vector store:** PostgreSQL + pgvector local, cosine distance, bảng `day6_chunks`.
- **Lệnh chạy:** `python -m src.run` từ thư mục `starter`.
- **Chi phí/thời gian:** lần chạy pipeline thành công mất **55.07 giây**; CSV OpenRouter tương ứng ghi nhận **143,846 prompt tokens** và tổng chi phí embedding **$0.002870** cho toàn bộ A/B/C và query benchmark.
- **Metadata:** `document_id`, `source`, `page`, `year`, `section`, `has_text`, `physical_page`. Section suy ra từ header PDF; year lấy từ manifest và bằng 2026.

## Cấu hình và benchmark

- **A:** fixed-size khoảng 500 ký tự, overlap 50, không filter.
- **B:** chunk theo paragraph, giới hạn 1000 ký tự, không filter.
- **C:** cùng chunking như B và filter metadata từ câu hỏi trước khi truy xuất.
- Cả ba dùng cùng corpus, embedding model, vector store metric và bộ câu hỏi.
- **Benchmark:** 20 câu trong `starter/benchmark/questions.json`, gồm 15 dev và 5 test; 5 câu metadata filter, trong đó 2 câu thuộc test. Mỗi câu có gold source/page và evidence quote.
- **Tiêu chí chọn:** ưu tiên Evidence Hit@3, sau đó Hit@1; grounding, coherence và chi phí/tài nguyên dùng để phân tích trade-off.

## Kết quả

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian | Chi phí |
|---|---|---:|---:|---:|---|---|
| A | dev | 2/15 | 3/15 | 637 | 55.07s toàn pipeline | $0.002870 toàn pipeline |
| A | test | 1/5 | 1/5 | 637 | 55.07s toàn pipeline | $0.002870 toàn pipeline |
| B | dev | 1/15 | 5/15 | 312 | 55.07s toàn pipeline | $0.002870 toàn pipeline |
| B | test | 0/5 | 0/5 | 312 | 55.07s toàn pipeline | $0.002870 toàn pipeline |
| C | dev | 2/15 | 5/15 | 312 | 55.07s toàn pipeline | $0.002870 toàn pipeline |
| C | test | 0/5 | 0/5 | 312 | 55.07s toàn pipeline | $0.002870 toàn pipeline |

Nguồn kết quả: `starter/results/summary.json`. Trace đầy đủ: `starter/results/traces.json`. Audit: `results/manual_audit.md`.

| Strategy | Coherence trung bình /2 (n) | Metadata đủ và đúng (n/N) | Filter tuân thủ (n/N hoặc N/A) | Grounding 0/1/2 |
|---|---|---|---|---|
| A | 1.0/2 (10) | 15/15 trên test top-3 | N/A | 9/10, trung bình 1.8/2 |
| B | 1.0/2 (10) | 15/15 trên test top-3 | N/A | 9/10, trung bình 1.8/2 |
| C | 1.0/2 (10) | 15/15 trên test top-3 | 15/15 trên các filter query | 9/10, trung bình 1.8/2 |

Audit thủ công được ghi tại `results/manual_audit.md`. Coherence được chấm bảo thủ vì B/C hiện vẫn phụ thuộc page block. Kiểm tra tự động trên trace cho thấy metadata bắt buộc đầy đủ ở 180/180 hit; riêng các filter query của C tuân thủ 15/15 hit.

## Phân tích và kết luận

- **A-B:** A có Hit@1 dev/test tốt hơn (2/15, 1/5 so với 1/15, 0/5), trong khi B có Evidence Hit@3 dev cao hơn (5/15 so với 3/15). Fixed-size overlap giữ khả năng top-1 tốt hơn; paragraph chunking đưa evidence vào top-3 dev nhiều hơn nhưng chưa ổn định trên test.
- **B-C:** C cải thiện Hit@1 dev từ 1/15 lên 2/15 và giữ Evidence Hit@3 dev ở 5/15; test vẫn 0/5. Filter metadata chưa chứng minh lợi ích tổng quát trên test.
- **Ví dụ lỗi:** evaluator tự động bỏ qua một số bằng chứng gần đúng do khác dấu câu/encoding (ví dụ q19 và El Niño ở q20); vì vậy grounding audit được báo cáo riêng, không thay đổi Hit@3 tự động.
- **Lựa chọn tạm thời:** A là strategy duy nhất có kết quả test dương. Tuy nhiên test chỉ có 5 câu nên kết luận chỉ áp dụng cho corpus này.
- **Hạn chế:** test nhỏ; runtime/chi phí chỉ được đo cho toàn pipeline, chưa tách riêng theo strategy; section metadata suy ra từ header; paragraph chunking phụ thuộc xuống dòng PDF; evaluator tự động không thay thế grounding thủ công.
- **Nếu làm lại:** audit thủ công trước, đo thời gian/chi phí, cải thiện tách heading-paragraph, kiểm thử thêm filter và giữ test set mới nếu đã điều chỉnh theo test cũ.
