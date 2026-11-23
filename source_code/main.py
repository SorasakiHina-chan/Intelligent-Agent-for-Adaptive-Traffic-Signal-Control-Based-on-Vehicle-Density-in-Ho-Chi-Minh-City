"""main.py - Điểm chạy trung tâm: chạy mô phỏng -> ghi results/ -> vẽ biểu đồ -> mở animation.

Chạy (trong thư mục source_code/):
    python main.py                                      # medium + adaptive
    python main.py --scenario high --method fixed
    python main.py --no-animation                       # chỉ tính toán + lưu file, không mở cửa sổ
    python main.py --runs 50                            # số lần chạy ngẫu nhiên để lấy trung bình
"""
import argparse
import csv
from pathlib import Path

from traffic_data import SCENARIOS, generate_traffic_data, get_default_output_path
from simulation import run_all_scenarios, run_multi_seed, summary_rows, print_table
from visualization import (animate_intersection, frames_from_history, plot_comparison,
                           plot_queue_over_time, plot_snapshot)

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name.lower() == "source_code" else SCRIPT_DIR
RESULTS_DIR = ROOT / "results"
CHARTS_DIR = RESULTS_DIR / "charts"


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as f:   # utf-8-sig để Excel mở không lỗi
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Đã lưu: {path}")


def main():
    parser = argparse.ArgumentParser(description="Mô phỏng đèn giao thông thích ứng")
    parser.add_argument("--scenario", choices=list(SCENARIOS), default="medium")
    parser.add_argument("--method", choices=["fixed", "adaptive"], default="adaptive")
    parser.add_argument("--runs", type=int, default=30, help="số lần chạy ngẫu nhiên để lấy trung bình")
    parser.add_argument("--no-animation", action="store_true", help="không mở cửa sổ animation")
    parser.add_argument("--speed", type=int, default=5, help="hiển thị mỗi N giây mô phỏng một khung")
    args = parser.parse_args()

    print("[1/4] Kiểm tra dữ liệu...")
    csv_path = get_default_output_path()
    if not csv_path.exists():
        generate_traffic_data(csv_path)

    print("[2/4] Chạy Fixed và Adaptive trên traffic_data.csv...")
    results = run_all_scenarios(csv_path)
    rows = summary_rows(results)
    print_table(rows)

    print(f"[3/4] Ghi kết quả và biểu đồ vào {RESULTS_DIR} ...")
    RESULTS_DIR.mkdir(exist_ok=True)
    for name in SCENARIOS:                                        # result_low.csv, result_medium.csv, result_high.csv
        write_csv(RESULTS_DIR / f"result_{name}.csv", [r for r in rows if r["scenario"] == name])
    write_csv(RESULTS_DIR / "results_average.csv", run_multi_seed(args.runs))
    plot_comparison(results, CHARTS_DIR / "comparison_chart.png")
    plot_queue_over_time(results["high"]["Fixed"], results["high"]["Adaptive"], "high", CHARTS_DIR / "queue_over_time_high.png")
    plot_snapshot(results["high"]["Fixed"], results["high"]["Adaptive"], "high", path=CHARTS_DIR / "snapshot_high.png")

    if args.no_animation:
        print("[4/4] Bỏ qua animation (--no-animation)")
    else:
        print("[4/4] Mở animation (bấm chuột vào cửa sổ để tạm dừng)...")
        frames = frames_from_history(results[args.scenario][args.method.capitalize()]["history"])
        animate_intersection(frames, title=f"{args.method.upper()} - kịch bản {args.scenario}", speed=args.speed)


if __name__ == "__main__":
    main()
