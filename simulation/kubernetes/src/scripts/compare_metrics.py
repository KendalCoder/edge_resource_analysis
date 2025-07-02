import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

def compute_node_metrics(task_log_path, scheduler_name):
    if not os.path.exists(task_log_path):
        print(f"[ERROR] Log file not found: {task_log_path}")
        return None

    df = pd.read_csv(task_log_path)

    if not {"task_id", "node_id", "start_time", "end_time", "energy_used_j"}.issubset(df.columns):
        print(f"[ERROR] Log file missing required columns: {task_log_path}")
        return None

    df["exec_time"] = df["end_time"] - df["start_time"]

    grouped = df.groupby("node_id").agg({
        "task_id": "count",
        "energy_used_j": "mean",
        "exec_time": "mean"
    }).reset_index()

    grouped.rename(columns={
        "task_id": "num_tasks",
        "energy_used_j": "mean_energy",
        "exec_time": "avg_task_time"
    }, inplace=True)

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
        print("[ERROR] No results to compare.")
        return None

    combined = pd.concat(all_results, ignore_index=True)

    # Save to CSV
    combined.to_csv("scheduler_comparison_metrics.csv", index=False)
    print("[INFO] Metrics comparison saved to scheduler_comparison_metrics.csv")

    return combined

def plot_metric(df, metric_name):
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x="node_id", y=metric_name, hue="scheduler")
    plt.title(f"{metric_name.replace('_', ' ').title()} per Node by Scheduler")
    plt.ylabel(metric_name.replace("_", " ").title())
    plt.xlabel("Node ID")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # List your scheduler names exactly as used in the filenames
    schedulers = ["WaggleScheduler", "FairshareScheduler"]
    
    # Directory where log files like WaggleScheduler_task_log.csv are stored
    log_directory = "logs"

    metrics_df = compare_schedulers(log_directory, schedulers)

    if metrics_df is not None:
        # Plot each metric
        for metric in ["mean_energy", "num_tasks", "avg_task_time"]:
            plot_metric(metrics_df, metric)


            