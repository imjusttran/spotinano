# Pulse Music

Ứng dụng desktop hiện đại để tìm và nghe nhạc từ tất cả nguồn đã kết nối trong một lần tìm kiếm.

## Có gì mới

- Tìm song song YouTube và SoundCloud.
- Mỗi kết quả hiển thị thumbnail của nguồn phát; ảnh tải nền nên không chặn giao diện.
- Phát bằng VLC trực tiếp từ luồng audio tốt nhất mà nguồn trả về. Không transcode, không nén lại, không tải file nhạc về máy.
- Có chọn bài, pause, stop, tua thanh thời gian, tua ±10 giây, bài trước/sau và âm lượng.
- UI Pulse editorial: nền tối sạch, tiêu đề mạnh, accent xanh lime, cover playlist lớn và player thanh ngang gọn.
- Thông báo xuất hiện ngay trong cửa sổ, tự ẩn sau 3 giây; nút **Thông báo** mở lịch sử đầy đủ thay vì chèn message vào giao diện.
- Tạo playlist ở sidebar; nhấp chuột phải lên bài để thêm vào hoặc, khi đang mở playlist, xóa chính bài đó khỏi playlist. Lịch sử ghi tối đa 30 bài đã bắt đầu phát.
- Kéo-thả bài trong playlist để đổi thứ tự, hoặc dùng menu chuột phải để đưa bài lên/xuống. Nút **Trộn playlist** chỉ thay đổi thứ tự phát hiện tại, không ghi đè playlist đã lưu.
- Playlist và lịch sử cũ thiếu thumbnail sẽ tự tải lại ảnh bìa; URL ảnh lỗi được thử lại bằng metadata mới của nguồn.
- Khi mở playlist có header riêng như Spotify: cover, số lượng bài, nút **Phát playlist** để phát từ bài đầu tiên và nút **Đổi ảnh bìa** để chọn ảnh PNG/JPG/WEBP từ máy. Playlist cũ tự động được nâng cấp và giữ nguyên bài hát.

## Chạy trên Windows

1. Cài Python 3.11+ và [VLC Media Player desktop](https://www.videolan.org/vlc/).
2. Mở PowerShell ngay trong thư mục này rồi chạy:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\run_windows.ps1
```

Script tự tạo `.venv` và cài các Python packages cần thiết. Không cần FFmpeg để chạy player.

Playlist, ảnh bìa và lịch sử được lưu cục bộ tại `%LOCALAPPDATA%\PulseMusic\library.json`.

## Tạo bản `.exe` độc lập

Trên máy dùng để build cần có VLC desktop, sau đó chạy:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_exe.ps1
```

File phát hành là `dist\PulseMusic.exe`. VLC runtime, Python và toàn bộ thư viện được nhúng trong file này; người nhận chỉ cần mở `.exe` và không cần cài Python hoặc VLC.

## Lưu ý

- Kết quả và quyền phát phụ thuộc vào mạng, khu vực và từng nền tảng. Hãy chỉ phát nội dung bạn có quyền truy cập.
- Nếu một nguồn đổi cơ chế, cập nhật yt-dlp bằng `.\.venv\Scripts\python.exe -m pip install -U yt-dlp`.

## Cài lệnh `spotifynano` bằng npm (Windows)

Máy build cần Node.js/npm. Chạy `.\build_exe.ps1` để tạo cả file chạy độc lập và gói cài npm tại `dist\spotifynano-1.0.0.tgz`. Trên máy muốn cài, mở terminal trong thư mục chứa gói rồi chạy:

```powershell
npm install -g .\spotifynano-1.0.0.tgz
spotifynano
```

Ứng dụng đã nhúng Python và VLC; Node.js/npm chỉ cần cho bước cài đặt và tạo lệnh gọi app.
