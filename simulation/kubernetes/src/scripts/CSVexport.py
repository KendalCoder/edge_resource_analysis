import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
from torch.utils.tensorboard import SummaryWriter
import time 

def tensorboard_to_csv(log_dir, output_csv):
    print(f"[INFO] Loading TensorBoard logs from: {log_dir}")
    ea = EventAccumulator(log_dir)
    ea.Reload()

    all_scalars = []

    for tag in ea.Tags().get('scalars', []):
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

    if not {"task_id", "node_id", "start_time", "end_time", "energy_used_j"}.issubset(df.columns):
        print(f"[ERROR] Missing required columns in: {task_log_path}")
        return None


    df["exec_time"] = df["end_time"] - df["start_time"]

    grouped = df.groupby("node_id").agg(
        num_tasks=('task_id', 'count'),
        mean_energy=('energy_used_j', 'mean'),
        total_energy=('energy_used_j', 'sum'),
        max_energy=('energy_used_j', 'max'),
        min_energy=('energy_used_j', 'min'),
        avg_task_time=('exec_time', 'mean'),
        std_task_time=('exec_time', 'std'),
        total_exec_time=('exec_time', 'sum')

    ).reset_index()
    # Optional CPU and Memory metrics
    if "cpu_percent" in df.columns:
        grouped["avg_cpu_percent"] = df.groupby("node_id")["cpu_percent"].mean().values
        grouped["max_cpu_percent"] = df.groupby("node_id")["cpu_percent"].max().values
    if "memory_mb" in df.columns:
        grouped["max_memory_mb"] = df.groupby("node_id")["memory_mb"].max().values
    # Efficiency = tasks per unit time
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


def summarize_overall_scheduler_performance(df):

    summary = df.groupby("scheduler").agg({
        "num_tasks": "sum",
        "total_energy": "sum",
        "avg_task_time": "mean",
        "task_efficiency": "mean"
    }).reset_index()

    print("\n=== Scheduler Summary ===")
    print(summary)
    return summary



# plot_metrics is not defined; use plot_metrics_per_scheduler instead
# plot_metrics(metrics_df, [
#     "mean_energy", "total_energy", "max_energy", "min_energy",
#     "num_tasks", "avg_task_time", "std_task_time", "task_efficiency",
#     "avg_cpu", "peak_memory_mb"])
# plot metrics, use the defined function:
# plot_metrics_per_scheduler(metrics_df)


def plot_metrics_per_scheduler(df, save_dir="plots"):
    os.makedirs(save_dir, exist_ok=True)


    # Summarize key metrics per scheduler

    summary = df.groupby("scheduler").agg({

        "num_tasks": "sum",

        "total_energy": "sum",

        "avg_task_time": "mean",

        "task_efficiency": "mean"

    }).reset_index()


    # Plot each metric

    for column in summary.columns[1:]:

        plt.figure(figsize=(8, 5))

        sns.barplot(data=summary, x="scheduler", y=column, palette="viridis")

        plt.title(f"{column.replace('_', ' ').title()} per Scheduler")

        plt.ylabel(column.replace('_', ' ').title())

        plt.xlabel("Scheduler")
        plt.tight_layout()


        plot_file = os.path.join(save_dir, f"{column}_per_scheduler.png")

        plt.savefig(plot_file)

        plt.close()

        print(f"[INFO] Saved: {plot_file}")


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
        return random.choice(log_folders)
    else:
        return base_dir  # fallback

if __name__ == "__main__":
    # === Part 1: Export TensorBoard scalars ===
    log_dir_event_file = "kubernetes/logs/20250702-171434/events.out.tfevents.1751494474.lemont"
    output_csv = "scheduler_metrics.csv"

    if os.path.exists(log_dir_event_file):
        tensorboard_to_csv(log_dir_event_file, output_csv)
    else:
        print(f"[ERROR] TensorBoard event file not found: {log_dir_event_file}")



    # === Part 2: Scheduler metrics & data (Task 2) ===
    # === Part 3: Scheduler log comparison (Task 3) ===
    log_dir_task = "logs"  # folder with task logs like WaggleScheduler_task_log.csv
    def simulate_scheduler_log(log_dir, scheduler_name, num_steps=10):
        path = os.path.join(log_dir, scheduler_name)
        os.makedirs(path, exist_ok=True)
        writer = SummaryWriter(log_dir=path)
        for step in range(num_steps):

            # Simulate scalar logs
            loss = 0.5 / (step + 1)
            energy = 50 + step * 2
            duration = 5 + (step % 3)

            writer.add_scalar("loss", loss, step)
            writer.add_scalar("energy_used", energy, step)
            writer.add_scalar("task_duration", duration, step)

            time.sleep(0.01)  # slight delay to vary timestamps
        writer.close()

        print(f"[INFO] Created log at: {path}")
if __name__ == "__main__":
    base_log_dir = "generated_logs"
    simulate_scheduler_log(base_log_dir, "WaggleScheduler")
    simulate_scheduler_log(base_log_dir, "FairshareScheduler")