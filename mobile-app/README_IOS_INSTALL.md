# Hướng dẫn chi tiết: Đóng gói và Cài đặt App Vietlott lên iPhone (iOS)

Dự án đã được tích hợp hoàn chỉnh nền tảng **Capacitor Native iOS** tại thư mục:
`D:\Thao\Vietlott\mobile-app`

Do bạn sử dụng máy tính **Windows** (không có máy Mac), Apple không cho phép biên dịch trực tiếp file `.ipa` ngay trên Windows. Tuy nhiên, chúng ta có giải pháp chuẩn quốc tế: **Dùng Cloud GitHub Actions (chạy máy Mac miễn phí trên Cloud) để tự động xuất file `.ipa`, sau đó tải về Windows và cắm cáp cài vào iPhone qua Sideloadly / AltStore**.

---

## BƯỚC 1: Xuất file `VietlottAnalytics.ipa` hoàn toàn tự động qua GitHub

Workflow tự động [build-ios.yml](file:///D:/Thao/Vietlott/.github/workflows/build-ios.yml) đã được tạo sẵn trong dự án.

1. **Khởi tạo và đẩy mã nguồn lên GitHub:**
   - Mở Terminal tại `D:\Thao\Vietlott`, chạy:
     ```bash
     git init
     git add .
     git commit -m "feat: setup mobile ios capacitor project"
     git branch -M main
     git remote add origin https://github.com/<tai-khoan-cua-ban>/vietlott.git
     git push -u origin main
     ```
2. **Kích hoạt Build trên GitHub:**
   - Vào repository trên GitHub của bạn $\rightarrow$ Chọn tab **Actions**.
   - Bấm vào workflow **Build iOS IPA** $\rightarrow$ Nhấn nút **Run workflow**.
   - GitHub sẽ cấp miễn phí 1 máy ảo macOS 14 để chạy Xcode, đóng gói toàn bộ ứng dụng và xuất ra file `VietlottAnalytics.ipa`.
3. **Tải file IPA về máy:**
   - Khi build xong (khoảng 2-3 phút, hiện tích xanh ✅), bấm vào lượt build đó.
   - Kéo xuống mục **Artifacts** $\rightarrow$ Tải file `VietlottAnalytics-IPA.zip` về máy tính $\rightarrow$ Giải nén ra được file `VietlottAnalytics.ipa`.

---

## BƯỚC 2: Cài đặt file IPA vào iPhone bằng Sideloadly trên Windows

**Sideloadly** là công cụ tốt nhất hiện nay trên Windows để cài app vào iPhone mà không cần bẻ khóa (Jailbreak):

1. **Tải công cụ cần thiết trên Windows:**
   - Tải và cài đặt **iTunes** (bản trực tiếp từ Apple, không tải từ Microsoft Store): [Tải iTunes Windows](https://www.apple.com/itunes/)
   - Tải và cài đặt **Sideloadly**: [https://sideloadly.io](https://sideloadly.io)
2. **Cắm cáp kết nối iPhone với máy tính:**
   - Mở màn hình iPhone, khi máy hỏi *"Tin cậy máy tính này?"* $\rightarrow$ Bấm **Tin cậy (Trust)** và nhập mật mã mở máy.
3. **Thực hiện cài đặt app:**
   - Mở phần mềm **Sideloadly** trên máy tính.
   - Kéo thả file `VietlottAnalytics.ipa` vào khung bên trái của Sideloadly.
   - Nhập địa chỉ **Apple ID** của bạn vào ô `Apple ID` (dùng để ký chứng chỉ cài cá nhân miễn phí).
   - Bấm nút **Start**. Nếu có mã xác thực 2 lớp (2FA) gửi về iPhone, hãy nhập vào máy tính.
   - Chờ khoảng 30 giây đến khi Sideloadly báo **Done!**
4. **Kích hoạt quyền chạy app trên iPhone (Chỉ làm lần đầu):**
   - Trên iPhone, vào **Cài đặt (Settings)** $\rightarrow$ **Cài đặt chung (General)** $\rightarrow$ **Quản lý VPN & Thiết bị (VPN & Device Management)**.
   - Chọn mục Apple ID của bạn $\rightarrow$ Nhấn **Tin cậy (Trust)**.
   - Vào **Cài đặt** $\rightarrow$ **Quyền riêng tư & Bảo mật (Privacy & Security)** $\rightarrow$ Kéo xuống dưới cùng bật **Chế độ nhà phát triển (Developer Mode)** (khởi động lại máy khi được hỏi).
   - Giờ bạn đã có thể mở app **Vietlott Analytics** ngay trên màn hình chính!

---

## BƯỚC 3: Kết nối App trên iPhone với Backend Máy Tính

Để app trên điện thoại tính toán được các thuật toán xác suất, dự báo kỳ quay và dàn số Bao:

1. **Đảm bảo iPhone và máy tính Windows cùng kết nối vào một mạng WiFi:**
   - Địa chỉ IP cục bộ của máy tính của bạn hiện tại là: `10.18.30.172` (hoặc kiểm tra lại bằng lệnh `ipconfig`).
2. **Khởi động server trên máy tính Windows:**
   ```powershell
   cd D:\Thao\Vietlott
   .\venv\Scripts\python.exe -m uvicorn src.app:app --host 0.0.0.0 --port 8000
   ```
   *(Tham số `--host 0.0.0.0` cho phép các thiết bị khác như iPhone trong mạng WiFi kết nối vào).*
3. **Cấu hình trên App iPhone:**
   - Khi mở app trên iPhone, ở góc trên bên phải thanh tiêu đề có nút biểu tượng bánh răng **⚙️ (Cài đặt máy chủ)**.
   - Mặc định app đã được thiết lập sẵn địa chỉ: `http://10.18.30.172:8000`.
   - Nếu bạn đổi mạng WiFi khác, chỉ cần bấm vào nút ⚙️ và nhập IP mới là app hoạt động mượt mà.
   - *(Nếu muốn ra ngoài đường dùng 4G mà vẫn mở app được, bạn chỉ cần dùng Cloudflare Tunnel miễn phí trỏ vào port 8000 rồi nhập link đó vào nút ⚙️).*
