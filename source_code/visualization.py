"""visualization.py - Toàn bộ phần VẼ: animation nút giao + biểu đồ so sánh (Thành viên 5).

Chạy thử:  python visualization.py --scenario high --method adaptive [--speed 5] [--save demo.gif] [--no-show]
Frame (mỗi giây 1 dict): {"time", "ns_light", "ew_light", "queue_ns", "queue_ew", "reason"}
"""
import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle, Rectangle

COLORS = {"GREEN": "#2ecc71", "YELLOW": "#f1c40f", "RED": "#e74c3c"}
MAX_CARS_PER_ARM = 11  # số xe tối đa vẽ trên mỗi nhánh (số xe thật vẫn hiện ở tiêu đề)
CAR_STEP = 0.7
METRICS = [("avg_waiting_time", "Thời gian chờ TB (s)"), ("avg_queue_length", "Hàng xe TB (xe)"),
           ("throughput", "Số xe đã qua (xe)"), ("total_delay", "Tổng trễ (xe·s)")]


def frames_from_history(history):
    """Đổi history của simulation.run_simulation() thành danh sách frame cho animation."""
    return [{"time": t, "queue_ns": qn, "queue_ew": qe, "ns_light": ln, "ew_light": le, "reason": r}
            for t, qn, qe, ln, le, r in history]


# ======================== ANIMATION ========================
def animate_intersection(frames, title="Nút giao", speed=5, save_path=None, show=True):
    """Vẽ nút giao 4 hướng chuyển động theo frames. Bấm chuột để tạm dừng / chạy tiếp."""
    if not frames:
        raise ValueError("Danh sách frames rỗng")
    frames = frames[::max(1, int(speed))]

    fig, ax = plt.subplots(figsize=(7, 7.5))
    ax.set(xlim=(-10, 10), ylim=(-10, 10), aspect="equal")
    ax.axis("off")
    ax.add_patch(Rectangle((-10, -1.5), 20, 3, color="#555555"))
    ax.add_patch(Rectangle((-1.5, -10), 3, 20, color="#555555"))

    lamps = {}
    for key, (x, y, label) in {"ns_light": (3.2, 3.2, "Bắc–Nam"), "ew_light": (-3.2, 3.2, "Đông–Tây")}.items():
        lamps[key] = Circle((x, y), 0.6, ec="black")
        ax.add_patch(lamps[key])
        ax.text(x, y - 1.1, label, ha="center", fontsize=9)

    # vị trí xe thứ i trên từng nhánh, tính từ vạch dừng
    arms = {"north": lambda i: (0.75, 1.8 + i * CAR_STEP), "south": lambda i: (-0.75, -1.8 - i * CAR_STEP),
            "east": lambda i: (1.8 + i * CAR_STEP, -0.75), "west": lambda i: (-1.8 - i * CAR_STEP, 0.75)}
    cars = {}
    for arm, pos in arms.items():
        w, h = (0.8, 0.5) if arm in ("north", "south") else (0.5, 0.8)
        cars[arm] = [Rectangle((pos(i)[0] - w / 2, pos(i)[1] - h / 2), w, h, color="#2980b9", visible=False)
                     for i in range(MAX_CARS_PER_ARM)]
        for car in cars[arm]:
            ax.add_patch(car)
    heading = ax.set_title("", fontsize=10)

    def show_cars(arm, count):
        for i, car in enumerate(cars[arm]):
            car.set_visible(i < count)

    def update(index):
        f = frames[index]
        for key, lamp in lamps.items():
            lamp.set_facecolor(COLORS[f[key]])
        show_cars("north", math.ceil(f["queue_ns"] / 2))   # hàng của 1 trục chia đều 2 chiều
        show_cars("south", f["queue_ns"] // 2)
        show_cars("east", math.ceil(f["queue_ew"] / 2))
        show_cars("west", f["queue_ew"] // 2)
        heading.set_text(f"{title}\nt = {f['time']} s | Xe chờ: Bắc–Nam {f['queue_ns']}, Đông–Tây {f['queue_ew']}"
                         f"\nLý do quyết định: {f.get('reason', '-')}")

    anim = FuncAnimation(fig, update, frames=len(frames), interval=100, repeat=False)
    paused = {"on": False}

    def toggle(_event):
        paused["on"] = not paused["on"]
        anim.pause() if paused["on"] else anim.resume()

    fig.canvas.mpl_connect("button_press_event", toggle)
    if save_path:
        anim.save(str(save_path), writer=PillowWriter(fps=10))
        print(f"Đã lưu animation: {save_path}")
    if show:
        plt.show()
    return fig, anim


# ======================== BIỂU ĐỒ ========================
def _save(fig, path, show):
    fig.tight_layout()
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150)
        print(f"Đã lưu biểu đồ: {path}")
    plt.show() if show else plt.close(fig)


def plot_comparison(results, path=None, show=False):
    """Cột so sánh Fixed và Adaptive. results = {scenario: {"Fixed": {...}, "Adaptive": {...}}} (từ simulation.py)."""
    names = list(results)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    w = 0.38
    for ax, (key, label) in zip(axes.flat, METRICS):
        xs = range(len(names))
        ax.bar([x - w / 2 for x in xs], [results[n]["Fixed"][key] for n in names], w, label="Đèn cố định", color="#e67e22")
        ax.bar([x + w / 2 for x in xs], [results[n]["Adaptive"][key] for n in names], w, label="Tác tử thích ứng", color="#27ae60")
        ax.set_xticks(list(xs))
        ax.set_xticklabels(names)
        ax.set_title(label)
        ax.legend()
    fig.suptitle("So sánh điều khiển cố định và thích ứng")
    _save(fig, path, show)


def plot_queue_over_time(res_fixed, res_adaptive, scenario, path=None, show=False):
    """Số xe chờ theo thời gian của 2 phương pháp (cùng một kịch bản)."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, res, name in zip(axes, (res_fixed, res_adaptive), ("Đèn cố định", "Tác tử thích ứng")):
        h = res["history"]
        ax.plot([x[0] for x in h], [x[1] for x in h], label="Bắc–Nam")
        ax.plot([x[0] for x in h], [x[2] for x in h], label="Đông–Tây")
        ax.set_title(f"{name} - kịch bản {scenario}")
        ax.set_xlabel("Thời gian (s)")
        ax.legend()
    axes[0].set_ylabel("Số xe chờ")
    _save(fig, path, show)


def draw_intersection(ax, frame, title):
    """Ảnh tĩnh nút giao tại 1 thời điểm (frame = 1 phần tử history)."""
    t, q_ns, q_ew, l_ns, l_ew = frame[:5]
    ax.add_patch(Rectangle((-1.2, -10), 2.4, 20, color="#555"))
    ax.add_patch(Rectangle((-10, -1.2), 20, 2.4, color="#555"))
    ax.add_patch(Circle((1.8, -1.9), 0.5, color=COLORS[l_ns]))
    ax.add_patch(Circle((-1.9, 1.8), 0.5, color=COLORS[l_ew]))
    for i in range(min(q_ns, 26)):   # xe Bắc–Nam: 2 làn, xếp lên theo nhánh nam
        ax.add_patch(Rectangle((-0.9 + (i % 2), -2.2 - (i // 2) * 0.6), 0.7, 0.45, color="#0074d9"))
    for i in range(min(q_ew, 26)):   # xe Đông–Tây: 2 làn, xếp theo nhánh tây
        ax.add_patch(Rectangle((-2.2 - (i // 2) * 0.9, -0.9 + (i % 2)), 0.7, 0.45, color="#b10dc9"))
    ax.set(xlim=(-10, 10), ylim=(-10, 10), aspect="equal")
    ax.axis("off")
    ax.set_title(f"{title} | t={t}s | NS={q_ns} xe, EW={q_ew} xe")


def plot_snapshot(res_fixed, res_adaptive, scenario, t=240, path=None, show=False):
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.5))
    draw_intersection(axes[0], res_fixed["history"][t], "Đèn cố định")
    draw_intersection(axes[1], res_adaptive["history"][t], "Tác tử thích ứng")
    fig.suptitle(f"Nút giao - kịch bản {scenario}  (xanh dương: Bắc–Nam, tím: Đông–Tây)")
    _save(fig, path, show)


# ======================== CHẠY THỬ GIAO DIỆN ========================
def main():
    from simulation import METHODS, load_arrivals_csv, run_simulation   # import muộn để tránh vòng lặp import
    p = argparse.ArgumentParser(description="Demo giao diện mô phỏng đèn giao thông")
    p.add_argument("--scenario", choices=["low", "medium", "high"], default="medium")
    p.add_argument("--method", choices=["fixed", "adaptive"], default="adaptive")
    p.add_argument("--speed", type=int, default=5, help="Bỏ qua mỗi N giây để chạy nhanh hơn")
    p.add_argument("--save", help="Lưu animation ra file .gif")
    p.add_argument("--no-show", action="store_true", help="Không mở cửa sổ (chạy trên máy chủ)")
    a = p.parse_args()
    if a.no_show:
        plt.switch_backend("Agg")
    arrivals, init = load_arrivals_csv(a.scenario)
    result = run_simulation(METHODS[a.method.capitalize()](), arrivals, init)
    animate_intersection(frames_from_history(result["history"]), title=f"{a.method.upper()} - kịch bản {a.scenario}",
                         speed=a.speed, save_path=a.save, show=not a.no_show)


if __name__ == "__main__":
    main()
