"""
Giao dien mo phong va bieu do so sanh (visualization.py).
Phu trach: Thanh vien 5.

Dinh dang du lieu chung ("frame"), moi giay mot dict:
    {"time": int, "ns_light": "GREEN|YELLOW|RED", "ew_light": ...,
     "queue_ns": int, "queue_ew": int, "reason": str (tuy chon)}
Cac khoa ns_light, ew_light, reason trung voi dau ra cua agent.step().
"""

import argparse
import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle, Rectangle

COLORS = {"GREEN": "#2ecc71", "YELLOW": "#f1c40f", "RED": "#e74c3c"}
MAX_CARS_PER_ARM = 11  # so xe toi da ve tren moi nhanh (so xe that van hien o tieu de)
CAR_STEP = 0.7
METRICS = [
    ("avg_wait", "Average Waiting Time (s)"),
    ("avg_queue", "Average Queue Length (xe)"),
    ("throughput", "Throughput (xe)"),
    ("total_delay", "Total Delay (s)"),
]


# ======================== GIAO DIEN MO PHONG ========================
def _make_arms():
    """Vi tri xe cho 4 nhanh duong: (x, y) cua xe thu i, tinh tu vach dung."""
    return {
        "north": lambda i: (0.75, 1.8 + i * CAR_STEP),
        "south": lambda i: (-0.75, -1.8 - i * CAR_STEP),
        "east": lambda i: (1.8 + i * CAR_STEP, -0.75),
        "west": lambda i: (-1.8 - i * CAR_STEP, 0.75),
    }


def animate_intersection(frames, title="Nút giao", speed=5, save_path=None, show=True):
    """Ve nut giao 4 huong chuyen dong theo danh sach frames. Bam chuot de tam dung."""
    if not frames:
        raise ValueError("Danh sach frames rong")
    frames = frames[::max(1, int(speed))]

    fig, ax = plt.subplots(figsize=(7, 7.5))
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.add_patch(Rectangle((-10, -1.5), 20, 3, color="#555555"))
    ax.add_patch(Rectangle((-1.5, -10), 3, 20, color="#555555"))

    lamps = {}
    for key, (x, y, label) in {"ns_light": (3.2, 3.2, "Bắc–Nam"),
                               "ew_light": (-3.2, 3.2, "Đông–Tây")}.items():
        lamps[key] = Circle((x, y), 0.6, ec="black")
        ax.add_patch(lamps[key])
        ax.text(x, y - 1.1, label, ha="center", fontsize=9)

    cars = {}
    for arm, pos in _make_arms().items():
        cars[arm] = []
        for i in range(MAX_CARS_PER_ARM):
            x, y = pos(i)
            w, h = (0.8, 0.5) if arm in ("north", "south") else (0.5, 0.8)
            car = Rectangle((x - w / 2, y - h / 2), w, h, color="#2980b9", visible=False)
            ax.add_patch(car)
            cars[arm].append(car)

    heading = ax.set_title("", fontsize=10)

    def show_cars(arm, count):
        for i, car in enumerate(cars[arm]):
            car.set_visible(i < count)

    def update(index):
        f = frames[index]
        for key, lamp in lamps.items():
            lamp.set_facecolor(COLORS[f[key]])
        # Hang xe cua mot truc chia deu cho hai chieu (Bac/Nam, Dong/Tay)
        show_cars("north", math.ceil(f["queue_ns"] / 2))
        show_cars("south", f["queue_ns"] // 2)
        show_cars("east", math.ceil(f["queue_ew"] / 2))
        show_cars("west", f["queue_ew"] // 2)
        heading.set_text(
            f"{title}\nt = {f['time']} s | Xe chờ: Bắc–Nam {f['queue_ns']}, "
            f"Đông–Tây {f['queue_ew']}\nLý do quyết định: {f.get('reason', '-')}"
        )

    anim = FuncAnimation(fig, update, frames=len(frames), interval=100, repeat=False)

    paused = {"on": False}

    def toggle(_event):
        paused["on"] = not paused["on"]
        anim.pause() if paused["on"] else anim.resume()

    fig.canvas.mpl_connect("button_press_event", toggle)

    if save_path:
        anim.save(str(save_path), writer=PillowWriter(fps=10))
        print(f"Da luu animation: {save_path}")
    if show:
        plt.show()
    return fig, anim, update


# ======================== BIEU DO SO SANH ========================
def plot_comparison(results, out_dir=None, show=True):
    """
    Ve bieu do cot so sanh dieu khien co dinh va thich ung.
    results: {"low": {"fixed": {"avg_wait": ..., ...}, "adaptive": {...}}, "medium": ..., "high": ...}
    Cac khoa chi so: avg_wait, avg_queue, throughput, total_delay (do metrics.py cung cap).
    """
    scenarios = list(results)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    width = 0.38
    for ax, (key, label) in zip(axes.flat, METRICS):
        xs = range(len(scenarios))
        fixed = [results[s]["fixed"][key] for s in scenarios]
        adaptive = [results[s]["adaptive"][key] for s in scenarios]
        ax.bar([x - width / 2 for x in xs], fixed, width, label="Đèn cố định", color="#e67e22")
        ax.bar([x + width / 2 for x in xs], adaptive, width, label="Tác tử thích ứng", color="#27ae60")
        ax.set_xticks(list(xs))
        ax.set_xticklabels(scenarios)
        ax.set_title(label)
    fig.suptitle("So sánh điều khiển cố định và thích ứng")
    fig.legend(*axes.flat[0].get_legend_handles_labels(), loc="lower center", ncol=2)
    fig.tight_layout(rect=(0, 0.04, 1, 1))

    if out_dir:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / "comparison.png", dpi=150)
        print(f"Da luu bieu do: {out_dir / 'comparison.png'}")
    if show:
        plt.show()
    return fig


# ======================== DU LIEU THU CHO DEMO ========================
# Chi dung de chay thu giao dien khi chua co simulation.py cua Thanh vien 4.
# Khi co simulation.py, truyen danh sach frames cua no vao animate_intersection().
def _find_csv():
    here = Path(__file__).resolve().parent
    for folder in (here.parent / "data", here / "data"):
        path = folder / "traffic_data.csv"
        if path.exists():
            return path
    raise FileNotFoundError("Khong thay traffic_data.csv. Hay chay traffic_data.py truoc.")


def _fixed_lights(t):
    """Chu ky co dinh 66 giay: Bac-Nam xanh 30 + vang 3, Dong-Tay xanh 30 + vang 3."""
    phase = t % 66
    if phase < 30:
        return "GREEN", "RED"
    if phase < 33:
        return "YELLOW", "RED"
    if phase < 63:
        return "RED", "GREEN"
    return "RED", "YELLOW"


def build_demo_frames(scenario, method="adaptive"):
    """Phat lai du lieu xe den tu CSV, dieu khien bang den co dinh hoac AdaptiveTrafficAgent."""
    with _find_csv().open(encoding="utf-8") as file:
        rows = [r for r in csv.DictReader(file) if r["scenario"] == scenario]
    if not rows:
        raise ValueError(f"Kich ban khong hop le: {scenario}")

    agent = None
    if method == "adaptive":
        from agent import AdaptiveTrafficAgent
        agent = AdaptiveTrafficAgent()

    capacity = int(rows[0]["storage_capacity_vehicles_per_direction"])
    q_ns, q_ew = int(rows[0]["initial_queue_ns"]), int(rows[0]["initial_queue_ew"])
    frames = []
    for row in rows:
        t = int(row["time_step_s"])
        q_ns = min(capacity, q_ns + int(row["arrivals_ns"]))
        q_ew = min(capacity, q_ew + int(row["arrivals_ew"]))
        if agent:
            out = agent.step(q_ns, q_ew)
            ns, ew, reason = out["ns_light"], out["ew_light"], out["reason"]
        else:
            (ns, ew), reason = _fixed_lights(t), "Chu kỳ cố định"
        frames.append({"time": t, "ns_light": ns, "ew_light": ew,
                       "queue_ns": q_ns, "queue_ew": q_ew, "reason": reason})
        # Gia dinh giai phong 1 xe/giay khi den xanh (giong agent.py)
        if ns == "GREEN":
            q_ns = max(0, q_ns - 1)
        elif ew == "GREEN":
            q_ew = max(0, q_ew - 1)
    return frames


def main():
    parser = argparse.ArgumentParser(description="Demo giao dien mo phong den giao thong")
    parser.add_argument("--scenario", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--method", choices=["fixed", "adaptive"], default="adaptive")
    parser.add_argument("--speed", type=int, default=5, help="Bo qua moi N giay de chay nhanh hon")
    parser.add_argument("--save", help="Luu animation ra file .gif")
    parser.add_argument("--no-show", action="store_true", help="Khong mo cua so (chay tren may chu)")
    args = parser.parse_args()

    if args.no_show:
        plt.switch_backend("Agg")
    names = {"fixed": "Đèn cố định", "adaptive": "Tác tử thích ứng"}
    animate_intersection(build_demo_frames(args.scenario, args.method),
                         title=f"{names[args.method]} – kịch bản {args.scenario}",
                         speed=args.speed, save_path=args.save, show=not args.no_show)


if __name__ == "__main__":
    main()
