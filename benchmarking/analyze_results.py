import csv
from pathlib import Path


def load_stats(file_path):
    stats = {}
    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Name"] and row["Name"] != "Aggregated":
                stats[row["Name"]] = row
    return stats


def load_conflicts(file_path, target_task):
    conflicts = 0
    if not file_path.exists():
        return 0
    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Name"] == target_task and "409" in row["Error"]:
                conflicts += int(row["Occurrences"])
    return conflicts


def main():
    results_dir = Path(__file__).parent / "results"

    pessimistic_stats_file = results_dir / "pessimistic_stats.csv"
    pessimistic_fail_file = results_dir / "pessimistic_failures.csv"
    occ_stats_file = results_dir / "optimistic_stats.csv"
    occ_fail_file = results_dir / "optimistic_failures.csv"

    if not pessimistic_stats_file.exists() or not occ_stats_file.exists():
        print(f"Error: Missing stats files in {results_dir}")
        print(f"Found: {list(results_dir.glob('*.csv'))}")
        return

    pess_data = load_stats(pessimistic_stats_file)
    occ_data = load_stats(occ_stats_file)

    target_task = "hot_slots_booking"

    if target_task not in pess_data or target_task not in occ_data:
        print(f"Error: Task {target_task} not found in one or both result files.")
        return

    p = pess_data[target_task]
    o = occ_data[target_task]

    # Calculate conflicts specifically from failures file
    p_conflicts = load_conflicts(pessimistic_fail_file, target_task)
    o_conflicts = load_conflicts(occ_fail_file, target_task)

    # Helper to convert string to float safely
    def val(x):
        return float(x) if x else 0.0

    metrics = {
        "RPS": ("Requests/s", "Higher is better"),
        "Avg Latency (ms)": ("Average Response Time", "Lower is better"),
        "P95 Latency (ms)": ("95%", "Lower is better"),
        "P99 Latency (ms)": ("99%", "Lower is better"),
        "Total Requests": ("Request Count", "Higher is better"),
        "Conflict Rate (%)": (None, "Lower is better"),
        "Genuine Error Rate (%)": (None, "Lower is better"),
    }

    print(f"\n{'=' * 80}")
    print(f" PERFORMANCE COMPARISON: {target_task}")
    print(f"{'=' * 80}")
    print(f"{'Metric':<25} | {'Pessimistic':<15} | {'Optimistic':<15} | {'Winner'}")
    print(f"{'-' * 80}")

    for label, (col, goal) in metrics.items():
        if col:
            p_val = val(p[col])
            o_val = val(o[col])
        else:
            if label == "Conflict Rate (%)":
                p_val = (p_conflicts / val(p["Request Count"])) * 100
                o_val = (o_conflicts / val(o["Request Count"])) * 100
            else:  # Genuine Error Rate
                p_genuine = val(p["Failure Count"]) - p_conflicts
                o_genuine = val(o["Failure Count"]) - o_conflicts
                p_val = (p_genuine / val(p["Request Count"])) * 100
                o_val = (o_genuine / val(o["Request Count"])) * 100

        if p_val > o_val if "Higher" in goal else p_val < o_val:
            winner = "Pessimistic"
        elif p_val < o_val if "Higher" in goal else p_val > o_val:
            winner = "Optimistic"
        else:
            winner = "Draw"

        # Format numbers
        if isinstance(p_val, float):
            p_str = f"{p_val:.2f}"
            o_str = f"{o_val:.2f}"
        else:
            p_str = str(p_val)
            o_str = str(o_val)

        print(f"{label:<25} | {p_str:<15} | {o_str:<15} | {winner}")

    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
