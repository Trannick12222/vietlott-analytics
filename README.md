# Vietlott Analytics

## 1. Giới thiệu dự án (Project Description)
Vietlott Analytics là một hệ thống phân tích, thống kê và mô phỏng kết quả xổ số Vietlott (tập trung vào Mega 6/45 và Power 6/55) dựa trên các phương pháp toán học và thống kê học. Ứng dụng cung cấp các góc nhìn phân tích sâu, điểm số mô hình cho các bộ số, và đánh giá thông qua backtesting. 

**Lưu ý quan trọng:** Hệ thống này hoàn toàn dành cho mục đích nghiên cứu dữ liệu, học thuật và giải trí. Nó KHÔNG mang ý nghĩa dự đoán chính xác kết quả tương lai, do bản chất ngẫu nhiên độc lập của các kỳ quay xổ số.

## 2. Tính năng (Features)
- Phân tích tần suất và độ trễ (Frequency & Recency) của các con số.
- Đánh giá phân phối (Chẵn/Lẻ, Cao/Thấp).
- Ước lượng Bayes và Mô phỏng Monte Carlo để xây dựng phân phối xác suất tham khảo.
- Động cơ chấm điểm tổng hợp (Ensemble Scoring Engine) để đánh giá sức mạnh tương đối của một bộ số.
- Cung cấp API mạnh mẽ để tích hợp với các hệ thống frontend khác.
- Hỗ trợ triển khai nhanh chóng với Docker & Docker Compose.
- Giao diện người dùng tích hợp sẵn sử dụng FastAPI, HTMX và Tailwind CSS.

## 3. Cài đặt và Chạy cục bộ (Installation)
**Yêu cầu hệ thống:** Python 3.10+

1. **Clone repository:**
   ```bash
   git clone https://github.com/your-repo/vietlott-analytics.git
   cd vietlott-analytics
   ```

2. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Chạy ứng dụng dạng Desktop PC (Cửa sổ ứng dụng máy tính riêng):**
   - **Cách 1 (Nhanh nhất):** Nhấp đúp chuột vào shortcut **`Vietlott Analytics`** ngay trên màn hình nền (Desktop) của Windows.
   - **Cách 2:** Nhấp đúp file [`Chay_Vietlott_Khong_Cua_So_Den.vbs`](file:///D:/Thao/Vietlott/Chay_Vietlott_Khong_Cua_So_Den.vbs) để mở ứng dụng native không có cửa sổ console đen.
   - **Cách 3:** Nhấp đúp file [`Chay_Vietlott_PC.bat`](file:///D:/Thao/Vietlott/Chay_Vietlott_PC.bat) hoặc chạy lệnh:
     ```powershell
     .\venv\Scripts\python.exe desktop_app.py
     ```

4. **Chạy ứng dụng dạng Web Server truyền thống:**
   ```bash
   .\venv\Scripts\uvicorn src.app:app --reload
   ```

## 4. Triển khai với Docker (Docker Deployment)
Ứng dụng có thể được triển khai dễ dàng bằng Docker.

1. **Khởi chạy container:**
   ```bash
   docker-compose up -d
   ```
2. Truy cập ứng dụng tại: `http://localhost:8000`

## 5. Cấu hình (Configuration)
Tạo tệp `.env` dựa trên `.env.example`:
```
ENVIRONMENT=development
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///data/vietlott.db
MONTE_CARLO_SIMULATIONS=100000
DECAY_FACTOR=0.05
```

## 6. Tài liệu API (API Documentation)
Khi ứng dụng đang chạy, truy cập `http://localhost:8000/docs` để xem tài liệu Swagger đầy đủ.

*Các endpoint API chính:*
- `GET /api/health`: Kiểm tra trạng thái hệ thống.
- `GET /api/draws/{lottery_type}`: Lấy danh sách kỳ quay gần nhất (Query param: `limit=20`, `lottery_type` là `MEGA_645` hoặc `POWER_655`).
- `GET /api/statistics/{lottery_type}`: Lấy toàn bộ phân tích thống kê (tần suất, độ trễ gap, chẵn/lẻ, cao/thấp, cụm bucket, liên tiếp, tương quan cặp, Bayes, xác suất toán học).
- `GET /api/predictions/{lottery_type}?threshold=50`: Lấy bảng xếp hạng số đề xuất và bộ số kết hợp (Filter Model Score &ge; ngưỡng).
- `GET /api/backtest/{lottery_type}`: Chạy kiểm thử ngược rolling window so sánh Model với Random baseline.
- `POST /api/fetch`: Kích hoạt quá trình fetch và cập nhật dữ liệu.
  *Payload:* `{"lottery_type": "MEGA_645", "limit": 25}`
- `GET /api/dashboard/{lottery_type}`: Lấy toàn bộ dữ liệu tổng hợp cho giao diện dashboard trong 1 request duy nhất.

## 7. Kiến trúc hệ thống (Architecture Diagram)
```text
+-------------------------------------------------------------+
|                      User / Client                          |
+-------------------------------------------------------------+
                               | (HTTP)
+-------------------------------------------------------------+
|                      FastAPI (src.app)                      |
|  +--------------------+  +-------------------------------+  |
|  |     API Routes     |  | Templates (HTMX / Tailwind)   |  |
|  +--------------------+  +-------------------------------+  |
+-------------------------------------------------------------+
             |                            |
+--------------------------+  +-------------------------------+
|     Services Layer       |  |      Data / Fetcher Layer     |
| - Validation             |  | - SQLite Database             |
| - Statistics Engine      |  | - Vietlott Source (Web Scrap) |
| - Prediction & Scoring   |  | - Backtesting                 |
| - Monte Carlo Simulation |  | - Data Models                 |
+--------------------------+  +-------------------------------+
```

## 8. Phương pháp luận thống kê (Statistical Methodology)
- **Phân tích tần suất (Frequency Analysis):** Theo dõi số lần xuất hiện của từng con số trong một khoảng thời gian cụ thể (lịch sử dài hạn, trung hạn, ngắn hạn).
- **Mô hình Bayesian (Bayesian Estimation):** Cập nhật xác suất tiên nghiệm dựa trên bằng chứng dữ liệu (kết quả quay thực tế) để tính toán trung bình hậu nghiệm cho mỗi số.
- **Mô phỏng Monte Carlo:** Sinh ra hàng nghìn/triệu kỳ quay ảo tuân theo nguyên lý phân phối đều giả định, qua đó so sánh với số liệu thực tế để tìm kiếm các độ lệch chuẩn.
- **Động cơ chấm điểm (Ensemble Scoring):** Sử dụng phương pháp kết hợp nhiều chiến lược (tần suất, chuỗi liên tiếp, ML đơn giản) để gán trọng số và hợp nhất thành một điểm số cuối cùng.

## 9. Phương pháp luận "Dự đoán" (Prediction Methodology)
- **Điểm số mô hình (Model Score):** Điểm số được tính toán phản ánh độ "khớp" của một bộ số so với các mẫu hình trong quá khứ được hệ thống ghi nhận.
- **Mức độ tự tin (Confidence Level):** Là một chỉ số đánh giá mức độ nhất quán của các mô hình cơ sở. Nếu tất cả mô hình đều đánh giá cao một số, độ tự tin tăng lên.
- **Tại sao Model Score ≠ Xác suất thực (Probability):** Trong xổ số, mỗi kỳ quay là một biến cố độc lập. Theo toán học xác suất, mọi bộ số 6 số bất kỳ luôn có cơ hội trúng giải chính xác bằng nhau (ví dụ 1 trên 8,145,060 đối với Mega 6/45). Điểm số từ mô hình chỉ thể hiện mối quan hệ thống kê mô tả, KHÔNG thay đổi xác suất vật lý.

## 10. Backtesting (Kiểm thử ngược)
Hệ thống đi kèm module Backtesting cho phép chạy các chiến lược chọn số dựa trên dữ liệu lịch sử trong khoảng thời gian N, và kiểm tra kết quả đối với các kỳ quay N+1, N+2... Việc này giúp minh họa sự ngẫu nhiên và đánh giá xem một thuật toán cụ thể có độ lệch dương so với random uniform hay không.

## 11. Hạn chế (Limitations)
- **Quy mô mẫu nhỏ (Small Sample Size):** Dữ liệu xổ số Vietlott chưa đủ lớn (mới vài nghìn kỳ) để tạo ra các xu hướng thống kê hoàn toàn đáng tin cậy.
- **Tính độc lập thống kê:** Các máy quay cầu hoạt động độc lập và không có bộ nhớ về quá khứ. "Định luật số lớn" chỉ đúng khi số kỳ tiến tới vô cực.
- **Không có khả năng dự đoán:** Không một mô hình toán học hay học máy nào có thể dự đoán xổ số một cách tin cậy để kiếm lợi nhuận.

## 12. Miễn trừ trách nhiệm (Disclaimer)
**English:** This software is for educational, statistical research, and entertainment purposes only. The application does NOT predict lottery outcomes, nor does it guarantee any financial returns. Lottery games are games of pure chance. Please play responsibly.

**Tiếng Việt:** Phần mềm này chỉ dành cho mục đích giáo dục, nghiên cứu thống kê và giải trí. Ứng dụng KHÔNG dự đoán kết quả xổ số, cũng như không đảm bảo bất kỳ lợi nhuận tài chính nào. Xổ số là trò chơi hoàn toàn ngẫu nhiên. Xin hãy chơi có trách nhiệm.

## 13. Công nghệ sử dụng (Tech Stack)
- **Ngôn ngữ:** Python 3.11
- **Web Framework:** FastAPI
- **Cơ sở dữ liệu:** SQLite / SQLAlchemy
- **Khoa học dữ liệu:** Pandas, NumPy, SciPy, scikit-learn
- **Frontend:** Jinja2, HTMX, Tailwind CSS
- **Triển khai:** Docker

## 14. Kiểm thử (Testing)
Để chạy các bộ kiểm thử tự động, sử dụng `pytest`:
```bash
pytest tests/ -v
```

## 15. Giấy phép (License)
Dự án được phân phối dưới giấy phép MIT. Xem tệp LICENSE để biết thêm chi tiết.
