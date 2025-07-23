import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def summarize_overall_scheduler_performance(df):
    summary = df.groupby("scheduler").agg({
        "num_tasks": "sum",
        "total_energy": "sum",
        "avg_task_time": "mean",
        "task_efficiency": "mean"
    }).reset_index()

    print("\n=== Scheduler Summary ===")
    print(summary)


    # Plot using pandas
    ax = summary.plot(x="scheduler", kind="bar", figsize=(10, 6), title="Scheduler Comparison")
    ax.set_ylabel("Metric Value")
    ax.set_xlabel("Scheduler")
    plt.tight_layout()
    plt.savefig("scheduler_summary_pandas_plot.png")
    plt.show()

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

def compute_node_metrics(task_log_path, scheduler_name):
    if not os.path.exists(task_log_path):
        print(f"[ERROR] Log file not found: {task_log_path}")
        return None

    df = preprocess_fair_scheduler_log(task_log_path)

    

    if not {"step", "node_id", "energy_used_j"}.issubset(df.columns):
        print(f"[ERROR] Missing required columns in: {task_log_path}")
        return None


    # df["exec_time"] = df["end_time"] - df["start_time"]

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




def preprocess_fair_scheduler_log(input_csv):
    """
    Reads FairScheduler_task_log.csv and returns a DataFrame with columns:
    step, node_id, start_time, end_time, cpu, energy
    """
    df = pd.read_csv(input_csv)
    # Extract node_id from tag (first part before '-')
    df['node_id'] = df['tag'].apply(lambda x: x.split('-')[0])
    # Identify metric type
    df['metric'] = df['tag'].apply(lambda x: 'energy' if 'energy' in x else ('cpu' if 'cpu' in x else None))
    # Only keep rows with energy or cpu
    df = df[df['metric'].notnull()]
    # Pivot so each (step, node_id) has columns for cpu and energy
    pivot = df.pivot_table(index=['step', 'node_id'], columns='metric', values='value', aggfunc='first').reset_index()
    # Add start_time and end_time columns (empty for now)
    pivot['start_time'] = ''
    pivot['end_time'] = ''
    # Reorder columns
    pivot = pivot[['step', 'node_id', 'start_time', 'end_time', 'cpu', 'energy']]
    print(f"[INFO] Preprocessed DataFrame created from {input_csv}")
    return pivot

if __name__ == "__main__":
    # # Simulate dummy logs for two schedulers
    # simulate_scheduler_log("logs", "RandomScheduler")
    # simulate_scheduler_log("logs", "FairScheduler")

    # Preprocess the CSV


    # Compare them
    metrics_df = compare_schedulers("./", ["FairScheduler"])

    if metrics_df is not None:
        summarize_overall_scheduler_performance(metrics_df)
        plot_metrics_per_scheduler(metrics_df)