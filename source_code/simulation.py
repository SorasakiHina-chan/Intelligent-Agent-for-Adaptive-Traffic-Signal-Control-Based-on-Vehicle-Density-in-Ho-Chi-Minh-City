"""simulation.py - Mô phỏng nút giao: chạy 1 bộ điều khiển trên chuỗi xe đến, trả về chỉ số + lịch sử.

Chỉ TÍNH TOÁN, không vẽ, không ghi file (vẽ: visualization.py, ghi file: main.py).
Chạy thử riêng:  python simulation.py
"""
import csv
import random
from collections import deque

from traffic_data import (SCENARIOS, SIMULATION_TIME, TIME_STEP, STORAGE_CAPACITY,
                          get_arrival_rates, poisson_random, calculate_waiting_time,
                          generate_traffic_data, get_default_output_path)
from agent import AdaptiveTrafficAgent
from fixed_signal import FixedSignalController
from metrics import MetricsCollector

SERVICE_RATE = 1.0   # xe/giây khi đèn xanh (2 làn x 0.5), cùng giả định với agent.py
METHODS = {"Fixed": FixedSignalController, "Adaptive": AdaptiveTrafficAgent}
KEYS = ("avg_waiting_time", "avg_queue_length", "throughput", "total_delay",
        "vehicles_in_queue_at_end", "vehicles_lost", "switch_count")


# ---------------------------------------------------------------- dữ liệu vào
def load_arrivals_csv(scenario, csv_path=None):
    """Đọc số xe đến mỗi giây + hàng xe ban đầu từ data/traffic_data.csv."""
    path = csv_path or get_default_output_path()
    if not path.exists():
        generate_traffic_data(path)
    with path.open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["scenario"] == scenario]
    arrivals = [(int(r["arrivals_ns"]), int(r["arrivals_ew"])) for r in rows]
    return arrivals, (int(rows[0]["initial_queue_ns"]), int(rows[0]["initial_queue_ew"]))


def generate_arrivals(scenario, seed):
    """Sinh xe đến theo cùng mô hình Poisson nhưng seed khác (để chạy nhiều lần)."""
    rng = random.Random(seed)
    out = []
    for t in range(0, SIMULATION_TIME, TIME_STEP):
        r_ns, r_ew = get_arrival_rates(scenario, t)
        out.append((poisson_random(r_ns * TIME_STEP / 60, rng), poisson_random(r_ew * TIME_STEP / 60, rng)))
    c = SCENARIOS[scenario]
    return out, (c["initial_queue_ns"], c["initial_queue_ew"])


# ---------------------------------------------------------------- mô phỏng
def run_simulation(controller, arrivals, initial_queues, service_rate=SERVICE_RATE):
    """history: (t, hàng NS, hàng EW, đèn NS, đèn EW, lý do quyết định)."""
    controller.reset()
    q = {"NS": deque([0] * initial_queues[0]), "EW": deque([0] * initial_queues[1])}
    m = MetricsCollector()
    credit = {"NS": 0.0, "EW": 0.0}
    history = []

    for t, (a_ns, a_ew) in enumerate(arrivals):
        # 1) xe đến (hàng đầy thì xe bị tính là không vào được)
        for d, n in (("NS", a_ns), ("EW", a_ew)):
            for _ in range(n):
                m.record_arrival()
                if len(q[d]) < STORAGE_CAPACITY:
                    q[d].append(t)
                else:
                    m.record_lost()

        # 2) tác tử nhận hàng xe + thời gian chờ của xe đầu hàng, trả về màu đèn
        out = controller.step(queue_ns=len(q["NS"]), queue_ew=len(q["EW"]), dt=TIME_STEP,
                              ext_wait_ns=(t - q["NS"][0]) if q["NS"] else 0,
                              ext_wait_ew=(t - q["EW"][0]) if q["EW"] else 0)
        lights = {"NS": out["ns_light"], "EW": out["ew_light"]}

        # 3) xe rời hàng khi đèn xanh
        for d in ("NS", "EW"):
            if lights[d] == "GREEN":
                credit[d] += service_rate * TIME_STEP
                while credit[d] >= 1 and q[d]:
                    m.record_departure(calculate_waiting_time(q[d].popleft(), t))
                    credit[d] -= 1
            else:
                credit[d] = 0.0

        m.record_queue(len(q["NS"]), len(q["EW"]))
        history.append((t, len(q["NS"]), len(q["EW"]), lights["NS"], lights["EW"],
                        out.get("reason", "Chu kỳ cố định")))

    end = len(arrivals)
    res = m.summary([end - a for d in q for a in q[d]])
    res["switch_count"] = getattr(controller, "switch_count", 0)
    res["history"] = history
    return res


def run_all_scenarios(csv_path=None):
    """Chạy Fixed và Adaptive trên cùng dữ liệu CSV: {scenario: {method: result}}."""
    results = {}
    for name in SCENARIOS:
        arrivals, init = load_arrivals_csv(name, csv_path)
        results[name] = {m: run_simulation(cls(), arrivals, init) for m, cls in METHODS.items()}
    return results


def run_multi_seed(runs=30, base_seed=1000):
    """Trung bình nhiều lần chạy ngẫu nhiên (mỗi lần chỉ có ~100-300 xe nên 1 lần chạy dễ nhiễu)."""
    rows = []
    for name in SCENARIOS:
        acc = {m: dict.fromkeys(KEYS, 0.0) for m in METHODS}
        for s in range(runs):
            arrivals, init = generate_arrivals(name, base_seed + s)
            for m, cls in METHODS.items():
                r = run_simulation(cls(), arrivals, init)
                for k in KEYS:
                    acc[m][k] += r[k] / runs
        rows += [{"scenario": name, "method": m, "runs": runs, **{k: round(v, 2) for k, v in acc[m].items()}}
                 for m in METHODS]
    return rows


def summary_rows(results):
    """Làm phẳng results thành list dict (mỗi dòng = 1 kịch bản x 1 phương pháp) để ghi CSV / in bảng."""
    return [{"scenario": s, "method": m, **{k: round(r[k], 2) for k in KEYS}}
            for s, by_method in results.items() for m, r in by_method.items()]


def print_table(rows):
    print(f"{'scenario':<8} {'method':<9} {'AvgWait':>8} {'AvgQueue':>9} {'Thru':>7} {'TotalDelay':>11} {'Switch':>7} {'Lost':>5}")
    for r in rows:
        print(f"{r['scenario']:<8} {r['method']:<9} {r['avg_waiting_time']:>8} {r['avg_queue_length']:>9} "
              f"{r['throughput']:>7} {r['total_delay']:>11} {r['switch_count']:>7} {r['vehicles_lost']:>5}")


if __name__ == "__main__":
    print_table(summary_rows(run_all_scenarios()))
