# Tác tử thông minh điều khiển đèn giao thông thích ứng tại TP.HCM

So sánh **đèn cố định** (chu kỳ 30 s xanh mỗi hướng) với **tác tử thích ứng** (đổi pha theo số xe đang chờ) tại một nút giao 4 hướng, trên 3 kịch bản lưu lượng: `low`, `medium`, `high`.

## Chạy nhanh

```bash
cd source_code
python -m pip install -r requirements.txt
python main.py
```

`main.py` sẽ chạy mô phỏng, lưu kết quả và biểu đồ vào `results/`, rồi mở animation (bấm chuột để tạm dừng).

| Lệnh | Tác dụng |
|---|---|
| `python main.py --scenario high --method fixed` | chọn kịch bản (`low/medium/high`) và phương pháp (`fixed/adaptive`) cho animation |
| `python main.py --interval 800` | animation chậm hơn (mặc định 400 ms/khung, 1 khung = 1 giây mô phỏng) |
| `python main.py --speed 5` | animation nhanh hơn (bỏ qua 5 giây mỗi khung) |
| `python main.py --no-animation` | chỉ tính toán và lưu file, không mở cửa sổ |
| `python main.py --runs 50` | số lần chạy ngẫu nhiên để lấy trung bình (mặc định 30) |

## Các file

| File | Vai trò |
|---|---|
| `traffic_data.py` | thông số mô phỏng + sinh `data/traffic_data.csv` |
| `agent.py` | tác tử thích ứng (luật IF-THEN, 6 pha an toàn) |
| `fixed_signal.py` | đèn cố định (đối chứng) |
| `simulation.py` | mô phỏng nút giao |
| `metrics.py` | tính chỉ số đánh giá |
| `visualization.py` | animation và biểu đồ |
| `main.py` | chạy toàn bộ |

## Kết quả (thư mục `results/`)

- `result_low.csv`, `result_medium.csv`, `result_high.csv`: 1 lần chạy trên `traffic_data.csv`
- `results_average.csv`: trung bình nhiều lần chạy ngẫu nhiên (dùng cho báo cáo)
- `charts/`: biểu đồ so sánh, hàng xe theo thời gian, ảnh nút giao

Các cột: `avg_waiting_time` (s/xe), `avg_queue_length` (xe), `throughput` (xe đã qua), `total_delay` (xe·s), `vehicles_in_queue_at_end`, `vehicles_lost`, `switch_count`.

## Giả định

Xả 1 xe/giây khi đèn xanh; sức chứa 52 xe/hướng; đèn cố định không có đỏ toàn phần (tác tử có 1 s). Số liệu là mô hình giả định, không phải đo thực tế.
