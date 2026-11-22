"""
main.py - Diem chay trung tam cua du an Traffic Agent.
Thanh vien 1 phu trach tich hop.

Chay:
    python main.py
    python main.py --scenario high --method adaptive
    python main.py --scenario medium --method fixed --no-animation
"""
import argparse
import csv
from pathlib import Path

from traffic_data import SCENARIOS, generate_traffic_data, get_default_output_path
from simulation import (
    METHODS, load_arrivals_csv, run_simulation,
    plot_comparison, plot_queue_over_time, plot_snapshot,
)
from visualization import animate_intersection

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name.lower() == "source_code" else SCRIPT_DIR
RESULTS_DIR = ROOT / "results"
CHARTS_DIR = RESULTS_DIR / "charts"


def run_all_scenarios():
    """Chay Fixed va Adaptive tren cung du lieu cho ca 3 kich ban."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = get_default_output_path()
    if not csv_path.exists():
        print("[1/3] Chua co du lieu, dang tao traffic_data.csv...")
        generate_traffic_data(csv_path)

    results = {}
    output_rows = []
    for scenario in SCENARIOS:
        arrivals, initial_queues = load_arrivals_csv(scenario, csv_path)
        results[scenario] = {}
        for method, controller_class in METHODS.items():
            result = run_simulation(controller_class(), arrivals, initial_queues)
            results[scenario][method] = result
            output_rows.append({
                "scenario": scenario,
                "method": method,
                "avg_waiting_time": round(result["avg_waiting_time"], 2),
                "avg_queue_length": round(result["avg_queue_length"], 2),
                "throughput": result["throughput"],
                "total_delay": round(result["total_delay"], 2),
                "vehicles_in_queue_at_end": result["vehicles_in_queue_at_end"],
                "vehicles_lost": result["vehicles_lost"],
                "switch_count": result["switch_count"],
            })

    output_csv = RESULTS_DIR / "results.csv"
    with output_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)

    plot_comparison(results, str(CHARTS_DIR / "comparison_chart.png"))
    plot_queue_over_time(
        results["high"]["Fixed"], results["high"]["Adaptive"],
        "high", str(CHARTS_DIR / "queue_over_time_high.png")
    )
    plot_snapshot(
        results["high"]["Fixed"], results["high"]["Adaptive"],
        "high", path=str(CHARTS_DIR / "snapshot_high.png")
    )

    print("\n=== KET QUA SO SANH ===")
    print(f"{'Kich ban':<10}{'Phuong phap':<12}{'Cho TB (s)':>12}"
          f"{'Hang xe TB':>12}{'Xe qua':>10}{'Tong tre':>12}")
    for row in output_rows:
        print(f"{row['scenario']:<10}{row['method']:<12}"
              f"{row['avg_waiting_time']:>12.2f}"
              f"{row['avg_queue_length']:>12.2f}"
              f"{row['throughput']:>10}"
              f"{row['total_delay']:>12.2f}")

    print(f"\nDa luu bang ket qua: {output_csv}")
    print(f"Da luu bieu do trong: {CHARTS_DIR}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Mo phong den giao thong thich ung")
    parser.add_argument("--scenario", choices=list(SCENARIOS), default="medium")
    parser.add_argument("--method", choices=["fixed", "adaptive"], default="adaptive")
    parser.add_argument("--no-animation", action="store_true",
                        help="Chi chay tinh toan va tao bieu do, khong mo cua so animation")
    parser.add_argument("--speed", type=int, default=5,
                        help="Hien thi moi N giay mo phong mot khung")
    args = parser.parse_args()

    print("=== TRAFFIC AGENT PROJECT - THANH VIEN 1 ===")
    print("[1/3] Kiem tra va tao du lieu...")
    csv_path = get_default_output_path()
    if not csv_path.exists():
        generate_traffic_data(csv_path)

    print("[2/3] Tich hop va chay hai phuong phap...")
    results = run_all_scenarios()

    if not args.no_animation:
        print("[3/3] Mo phong truc quan...")
        selected = results[args.scenario][
            "Fixed" if args.method == "fixed" else "Adaptive"
        ]
        frames = [
            {
                "time": frame[0],
                "queue_ns": frame[1],
                "queue_ew": frame[2],
                "ns_light": frame[3],
                "ew_light": frame[4],
                "reason": args.method,
            }
            for frame in selected["history"]
        ]
        animate_intersection(
            frames,
            title=f"{args.method.upper()} - kich ban {args.scenario}",
            speed=args.speed,
            show=True,
        )
    else:
        print("[3/3] Bo qua animation theo tuy chon --no-animation")

    print("\nHOAN TAT. Hay kiem tra thu muc results/.")


if __name__ == "__main__":
    main()
