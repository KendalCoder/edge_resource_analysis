from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
import pandas as pd
import os

log_dir = "runs/20250702-095535 "  # Your log directory

# Check if the log directory exists before proceeding
if not os.path.exists(log_dir):
    raise FileNotFoundError(f"Log directory '{log_dir}' does not exist. Please check the path.")

def extract_scalar_events(log_dir):
    ea = EventAccumulator(log_dir)
    ea.Reload()

    scalar_data = {}

    for tag in ea.Tags()['scalars']:
        events = ea.Scalars(tag)
        scalar_data[tag] = [(e.step, e.value) for e in events]

    return scalar_data

def save_to_csv(scalar_data, output_dir="csv_output"):
    os.makedirs(output_dir, exist_ok=True)

    for tag, values in scalar_data.items():
        df = pd.DataFrame(values, columns=['Step', 'Value'])
        csv_path = os.path.join(output_dir, f"{tag.replace('/', '_')}.csv")
        df.to_csv(csv_path, index=False)
        print(f"Saved: {csv_path}")

scalar_data = extract_scalar_events(log_dir)
save_to_csv(scalar_data)