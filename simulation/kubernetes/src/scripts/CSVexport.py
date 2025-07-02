import os
import pandas as pd
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

log_dir = "home/kendal/edge_resource_analysis/simulation/kubernetes/runs/20250702-171434"  #log directory

# Check if the log directory exists before proceeding
if not os.path.exists(log_dir):
    print(f"[ERROR] Log directory '{log_dir}' does not exist. Please check the path.")
    

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
    print(f" Export complete. CSV saved to: {output_csv}")

def pick_log_dir(base_dir, strategy="latest"):
    # TODO: Implement logic to pick the log directory based on strategy
    # For now, just return the base_dir as a placeholder
    return base_dir

if __name__ == "__main__":
    # log folder path
    log_dir = pick_log_dir("runs", strategy="latest") # or random logs 
    output_csv = "waggle_scheduler_metrics.csv"

    if not os.path.exists(log_dir):
        print(f"[ERROR] Log directory not found: {log_dir}")
    else:
        tensorboard_to_csv(log_dir, output_csv)