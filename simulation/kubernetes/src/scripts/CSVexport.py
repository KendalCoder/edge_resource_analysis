import os
import pandas as pd
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
import matplotlib.pyplot as plt
import seaborn as sns

def tensorboard_to_csv(log_dir, output_csv):
    print(f"[INFO] Loading TensorBoard logs from: {log_dir}")

    ea = EventAccumulator(log_dir)
    ea.Reload()

    all_scalars = []

    for tag in ea.Tags()['scalars']:
        events = ea.Scalars(tag)
        for e in events:
            all_scalars.append({
                'step': e.step,
                'tag': tag,
                'value': e.value
            })

    if not all_scalars:
        print("[WARN] No scalar data found. Check if the log directory contains event files.")
        return

    df = pd.DataFrame(all_scalars)
    df.to_csv(output_csv, index=False)
    print(f"[INFO] Export complete. CSV saved to: {output_csv}")

def compute_node_metrics(task_log_path, scheduler_name):
    if not os.path.exists(task_log_path):
        print(f"[ERROR] Log file not found: {task_log_path}")
        return None

    df = pd.read_csv(task_log_path)

    required_columns = {"task_id", "node_id", "start_time", "end_time", "energy_used_j"}
    if not required_columns.issubset(df.columns):
        print(f"[ERROR] Log file missing required columns: {task_log_path}")
        return None

    df["exec_time"] = df["end_time"] - df["start_time"]

    grouped = df.groupby("node_id").agg(
        num_tasks=('task_id', 'count'),
        mean_energy=('energy_used_j', 'mean'),
        total_energy=('energy_used_j', 'sum'),
        avg_task_time=('exec_time', 'mean'),
        total_exec_time=('exec_time', 'sum')
    ).reset_index()

    grouped["task_efficiency"] = grouped["num_tasks"] / grouped["total_exec_time"]
    grouped["scheduler"] = scheduler_name

    return grouped

def compare_schedulers(log_dir, scheduler_list):
    all_results = []

    for scheduler in scheduler_list:
        log_path = os.path.join(log_dir, f"{scheduler}_task_log.csv")
        metrics = compute_node_metrics(log_path, scheduler)
        if metrics is not None:
            all_results.append(metrics)

    if not all_results:
        print("[ERROR] No scheduler data to compare.")
        return None

    combined = pd.concat(all_results, ignore_index=True)

    comparison_path = os.path.join(log_dir, "scheduler_comparison_metrics.csv")
    combined.to_csv(comparison_path, index=False)
    print(f"[INFO] Comparison metrics saved to: {comparison_path}")

    return combined

def plot_metrics(df, metric_list):
    for metric in metric_list:
        plt.figure(figsize=(10, 6))
        sns.barplot(data=df, x="node_id", y=metric, hue="scheduler")
        plt.title(f"{metric.replace('_', ' ').title()} per Node by Scheduler")
        plt.ylabel(metric.replace('_', ' ').title())
        plt.xlabel("Node ID")
        plt.tight_layout()
        plt.show()

def pick_log_dir(base_dir, strategy="latest"):
    log_folders = [
        os.path.join(base_dir, f) for f in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, f))
    ]
    if not log_folders:
        return None

    if strategy == "latest":
        return max(log_folders, key=os.path.getmtime)
    elif strategy == "random":
        import random
        return random.choice(log_folders)
    else:
        return base_dir  # fallback

if __name__ == "__main__":
    # === Part 1: Export TensorBoard scalars ===
    log_dir_event_file = "kubernetes/logs/20250702-171434/events.out.tfevents.1751494474.lemont"
    output_csv = "waggle_scheduler_metrics.csv"

    if os.path.exists(log_dir_event_file):
        tensorboard_to_csv(log_dir_event_file, output_csv)
    else:
        print(f"[ERROR] TensorBoard event file not found: {log_dir_event_file}")

    # === Part 2: Scheduler log comparison (Task 2 & 3) ===
    log_dir_task = "logs"  # folder with task logs like WaggleScheduler_task_log.csv
    schedulers = ["WaggleScheduler", "FairshareScheduler"]

    metrics_df = compare_schedulers(log_dir_task, schedulers)
    if metrics_df is not None:
        plot_metrics(metrics_df, ["mean_energy", "total_energy", "num_tasks", "avg_task_time", "task_efficiency"])