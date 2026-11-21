"""
main.py - Chương trình điều phối chính của hệ thống mô phỏng đèn tín hiệu giao thông
thích ứng với mật độ phương tiện tại TP.HCM.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent if CURRENT_DIR.name.lower() == "source_code" else CURRENT_DIR

for p in (str(CURRENT_DIR), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from traffic_data import (  # noqa: E402
    SCENARIOS,
    generate_traffic_data,
    get_default_output_path,
)
from fixed_signal import FixedSignalController  # noqa: E402
from agent import AdaptiveTrafficAgent  # noqa: E402
from simulation import (  # noqa: E402
    METHODS,
    SERVICE_RATE,
    generate_arrivals,
    load_arrivals_csv,
    plot_comparison,
    plot_queue_over_time,
    plot_snapshot,
    run_simulation,
)

SUMMARY_KEYS = (
    "avg_waiting_time",
    "avg_queue_length",
    "throughput",
    "total_delay",
    "vehicles_in_queue_at_end",
    "vehicles_lost",
    "switch_count",
)


def get_project_paths() -> dict[str, Path]:
    """Khởi tạo các đường dẫn chuẩn theo cấu trúc thư mục dự án."""
    results_dir = PROJECT_ROOT / "results"
    charts_dir = PROJECT_ROOT / "charts"
    results_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)

    return {
        "data_csv": get_default_output_path(),
        "results_dir": results_dir,
        "charts_dir": charts_dir,
    }


def write_scenario_result_csv(
    output_path: Path,
    fixed_res: dict[str, Any],
    adaptive_res: dict[str, Any],
) -> None:
    """Ghi kết quả từng kịch bản ra results/result_<scenario>.csv."""
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "fixed_signal", "adaptive_agent"])
        for key in SUMMARY_KEYS:
            writer.writerow([
                key,
                round(fixed_res[key], 2),
                round(adaptive_res[key], 2),
            ])


def run_by_scenario(
    target_scenarios: tuple[str, ...],
    data_csv: Path,
    results_dir: Path,
    service_rate: float = SERVICE_RATE,
) -> dict[str, dict[str, dict[str, Any]]]:
    """Chạy Fixed và Adaptive trên cùng dữ liệu CSV của từng kịch bản."""
    if not data_csv.exists():
        generate_traffic_data(data_csv)

    results: dict[str, dict[str, dict[str, Any]]] = {}
    for scenario in target_scenarios:
        arrivals, init_queues = load_arrivals_csv(scenario, data_csv)
        fixed_res = run_simulation(
            FixedSignalController(), arrivals, init_queues, service_rate=service_rate
        )
        adaptive_res = run_simulation(
            AdaptiveTrafficAgent(), arrivals, init_queues, service_rate=service_rate
        )
        results[scenario] = {
            "Fixed": fixed_res,
            "Adaptive": adaptive_res,
        }
        write_scenario_result_csv(
            results_dir / f"result_{scenario}.csv", fixed_res, adaptive_res
        )
    return results


def run_multi_seed_average(
    target_scenarios: tuple[str, ...],
    runs: int,
    results_dir: Path,
    service_rate: float = SERVICE_RATE,
) -> list[dict[str, Any]]:
    """Chạy nhiều seed ngẫu nhiên để tính trung bình và lưu results_average.csv."""
    avg_rows: list[dict[str, Any]] = []
    for scenario in target_scenarios:
        acc = {m: {k: 0.0 for k in SUMMARY_KEYS} for m in METHODS}
        for s in range(runs):
            arrivals, init_queues = generate_arrivals(scenario, 1000 + s)
            for method_name, controller_cls in METHODS.items():
                res = run_simulation(
                    controller_cls(), arrivals, init_queues, service_rate=service_rate
                )
                for key in SUMMARY_KEYS:
                    acc[method_name][key] += res[key] / runs

        for method_name in METHODS:
            row = {
                "scenario": scenario,
                "method": method_name,
                "runs": runs,
                **{k: round(acc[method_name][k], 2) for k in SUMMARY_KEYS},
            }
            avg_rows.append(row)

    avg_csv = results_dir / "results_average.csv"
    with avg_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(avg_rows[0].keys()))
        writer.writeheader()
        writer.writerows(avg_rows)

    return avg_rows


def generate_charts_and_ui(
    results: dict[str, dict[str, dict[str, Any]]],
    charts_dir: Path,
    show_ui: bool = False,
) -> None:
    """Xuất biểu đồ vào thư mục charts/ và gọi visualization.py nếu có."""
    plot_comparison(results, path=str(charts_dir / "comparison_chart.png"))

    focus_scenario = "high" if "high" in results else next(iter(results))
    plot_queue_over_time(
        results[focus_scenario]["Fixed"],
        results[focus_scenario]["Adaptive"],
        focus_scenario,
        path=str(charts_dir / f"queue_over_time_{focus_scenario}.png"),
    )
    plot_snapshot(
        results[focus_scenario]["Fixed"],
        results[focus_scenario]["Adaptive"],
        focus_scenario,
        path=str(charts_dir / f"snapshot_{focus_scenario}.png"),
    )

    try:
        import visualization  # type: ignore

        if hasattr(visualization, "plot_comparison_charts"):
            visualization.plot_comparison_charts(results, output_dir=str(charts_dir))
        if show_ui and hasattr(visualization, "launch_demo_ui"):
            visualization.launch_demo_ui(results)
    except ImportError:
        if show_ui:
            print("[Lưu ý] Chưa có file visualization.py của Thành viên 5 để mở giao diện.")


def print_console_summary(
    results: dict[str, dict[str, dict[str, Any]]],
    avg_rows: list[dict[str, Any]] | None = None,
) -> None:
    """In bảng kết quả ra terminal để tiện kiểm tra nhanh."""
    print("\n=== KẾT QUẢ TRÊN DỮ LIỆU KỊCH BẢN (1 LẦN CHẠY) ===")
    print(
        f"{'scenario':<8} {'method':<9} {'AvgWait':>8} {'AvgQueue':>9} "
        f"{'Thru':>6} {'TotalDelay':>11} {'Switch':>6} {'Lost':>5}"
    )
    for scenario, pair in results.items():
        for method_name in ("Fixed", "Adaptive"):
            r = pair[method_name]
            print(
                f"{scenario:<8} {method_name:<9} "
                f"{r['avg_waiting_time']:>8.2f} {r['avg_queue_length']:>9.2f} "
                f"{r['throughput']:>6} {r['total_delay']:>11.2f} "
                f"{r['switch_count']:>6} {r['vehicles_lost']:>5}"
            )

    if avg_rows:
        runs = avg_rows[0]["runs"]
        print(f"\n=== TRUNG BÌNH {runs} LẦN CHẠY (MULTI-SEED) ===")
        for r in avg_rows:
            print(
                f"{r['scenario']:<8} {r['method']:<9} "
                f"{r['avg_waiting_time']:>8.2f} {r['avg_queue_length']:>9.2f} "
                f"{r['throughput']:>8.2f} {r['total_delay']:>11.2f} "
                f"{r['switch_count']:>6.2f} {r['vehicles_lost']:>5.2f}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Điều phối mô phỏng đèn tín hiệu giao thông thích ứng tại TP.HCM."
    )
    parser.add_argument(
        "--scenario",
        choices=["all", *SCENARIOS.keys()],
        default="all",
        help="Chọn kịch bản: low, medium, high hoặc all (mặc định: all).",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=30,
        help="Số lần chạy ngẫu nhiên để tính trung bình (mặc định: 30; đặt 0 để bỏ qua).",
    )
    parser.add_argument(
        "--service-rate",
        type=float,
        default=SERVICE_RATE,
        help=f"Tốc độ thông xe khi đèn xanh (xe/s, mặc định: {SERVICE_RATE}).",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Gọi giao diện từ visualization.py (nếu đã được Thành viên 5 thêm vào).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = get_project_paths()
    target_scenarios = tuple(SCENARIOS.keys()) if args.scenario == "all" else (args.scenario,)

    results = run_by_scenario(
        target_scenarios=target_scenarios,
        data_csv=paths["data_csv"],
        results_dir=paths["results_dir"],
        service_rate=args.service_rate,
    )

    avg_rows = None
    if args.runs > 0:
        avg_rows = run_multi_seed_average(
            target_scenarios=target_scenarios,
            runs=args.runs,
            results_dir=paths["results_dir"],
            service_rate=args.service_rate,
        )

    print_console_summary(results, avg_rows=avg_rows)
    generate_charts_and_ui(results, charts_dir=paths["charts_dir"], show_ui=args.ui)

    print(f"\nHoàn tất! File kết quả tại: {paths['results_dir']} | Biểu đồ tại: {paths['charts_dir']}")


if __name__ == "__main__":
    main()