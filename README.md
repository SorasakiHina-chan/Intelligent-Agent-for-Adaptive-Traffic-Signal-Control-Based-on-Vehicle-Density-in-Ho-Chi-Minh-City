# Tác tử thông minh điều khiển đèn giao thông thích ứng tại TP.HCM

So sánh điều khiển đèn **cố định** với **tác tử thích ứng theo mật độ xe** trên `low`, `medium`, `high`.

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy demo giao diện

Chạy trong thư mục `source_code/`:

```bash
python traffic_data.py                      # tạo data/traffic_data.csv (nếu chưa có)
python visualization.py --scenario high --method adaptive
python visualization.py --scenario high --method fixed
```

Tùy chọn: `--speed N` (bỏ qua mỗi N giây cho nhanh, mặc định 5), `--save demo.gif` (lưu ảnh động), `--no-show` (không mở cửa sổ). Bấm chuột vào cửa sổ để tạm dừng / chạy tiếp.

## Vẽ biểu đồ so sánh

```python
from visualization import plot_comparison
plot_comparison(results, out_dir="../results/charts")
```

`results` do `metrics.py` trả về, dạng:
`{"low": {"fixed": {...}, "adaptive": {...}}, "medium": ..., "high": ...}`
với mỗi dict gồm 4 khóa `avg_wait`, `avg_queue`, `throughput`, `total_delay`.

## Cho simulation.py ghép với giao diện

Mỗi giây trả về một dict, giao diện vẽ trực tiếp (khóa `ns_light`, `ew_light`, `reason` lấy từ `agent.step()`):

```python
{"time": 0, "ns_light": "GREEN", "ew_light": "RED",
 "queue_ns": 5, "queue_ew": 3, "reason": "HOLD_SERVING"}
```

Sau đó gọi `animate_intersection(frames, title="...")`.

## Lưu ý

Chế độ `--scenario/--method` chỉ phát lại dữ liệu xe đến trong CSV để thử giao diện, chưa phải kết quả thực nghiệm. Số liệu báo cáo phải lấy từ `simulation.py` và `metrics.py`.
