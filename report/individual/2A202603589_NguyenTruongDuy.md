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
- **Chi phí/thời gian:** chưa ghi log định lượng trong lần chạy này; cần bổ sung trước khi nộp nếu yêu cầu.
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
| A | dev | 2/15 | 3/15 | 637 | Chưa ghi | Chưa ghi |
| A | test | 1/5 | 1/5 | 637 | Chưa ghi | Chưa ghi |
| B | dev | 1/15 | 5/15 | 312 | Chưa ghi | Chưa ghi |
| B | test | 0/5 | 0/5 | 312 | Chưa ghi | Chưa ghi |
| C | dev | 2/15 | 5/15 | 312 | Chưa ghi | Chưa ghi |
| C | test | 0/5 | 0/5 | 312 | Chưa ghi | Chưa ghi |

Nguồn kết quả: `starter/results/summary.json`. Trace đầy đủ: `starter/results/traces.json`.

| Strategy | Coherence trung bình /2 (n) | Metadata đủ và đúng (n/N) | Filter tuân thủ (n/N hoặc N/A) | Grounding 0/1/2 |
|---|---|---|---|---|
| A | Chưa audit | Chưa audit | Chưa audit | Chưa audit |
| B | Chưa audit | Chưa audit | Chưa audit | Chưa audit |
| C | Chưa audit | Chưa audit | Chưa audit | Chưa audit |

Audit thủ công coherence 10 vị trí/strategy và grounding 5 câu test/strategy chưa được thực hiện, nên không điền số giả.

## Phân tích và kết luận

- **A-B:** A có Hit@1 dev/test tốt hơn (2/15, 1/5 so với 1/15, 0/5), trong khi B có Evidence Hit@3 dev cao hơn (5/15 so với 3/15). Fixed-size overlap giữ khả năng top-1 tốt hơn; paragraph chunking đưa evidence vào top-3 dev nhiều hơn nhưng chưa ổn định trên test.
- **B-C:** C cải thiện Hit@1 dev từ 1/15 lên 2/15 và giữ Evidence Hit@3 dev ở 5/15; test vẫn 0/5. Filter metadata chưa chứng minh lợi ích tổng quát trên test.
- **Ví dụ lỗi:** q17, q18 và q19 không có Evidence Hit@3 trên test ở cả ba strategy; q20 cũng không có hit. Cần kiểm tra trace, gold evidence và retrieval, không tự sửa nhãn sau khi xem kết quả.
- **Lựa chọn tạm thời:** A là strategy duy nhất có kết quả test dương. Tuy nhiên test chỉ có 5 câu nên kết luận chỉ áp dụng cho corpus này.
- **Hạn chế:** test nhỏ; chưa ghi thời gian/chi phí; section metadata suy ra từ header; paragraph chunking phụ thuộc xuống dòng PDF; evaluator tự động không thay thế grounding thủ công.
- **Nếu làm lại:** audit thủ công trước, đo thời gian/chi phí, cải thiện tách heading-paragraph, kiểm thử thêm filter và giữ test set mới nếu đã điều chỉnh theo test cũ.
