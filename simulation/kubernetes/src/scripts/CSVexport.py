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
    log_dir_event_file = "kubernetes/logs/20250723-111951-FairShareScheduler"  # Path to the TensorBoard event file
    # Note: Adjust the path to your actual TensorBoard event file location
    output_csv = "FairShareScheduler_task_log.csv"

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


