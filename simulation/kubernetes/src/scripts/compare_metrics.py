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



    

             # === Part 2: Scheduler metrics & data (Task 2) ===
    # === Part 3: Scheduler log comparison (Task 3) ===
    log_dir_task = "logs"  # folder with task logs like WaggleScheduler_task_log.csv
    schedulers = ["WaggleScheduler", "FairshareScheduler"]

    metrics_df = compare_schedulers(log_dir_task, schedulers)
    if metrics_df is not None:
        plot_metrics_per_scheduler(metrics_df)