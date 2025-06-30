from .scheduler import Scheduler


# Assigns jobs to a random node, irrespective of its load
class FairshareScheduler(Scheduler):
    def __init__(self):
        self.name = "fairshare-scheduler"
    
    def schedule(self, tally, workload, nodes: list):
        # find the least busy node and assign it the job
        cpu_usage = [node.metrics.get("cpu", float("inf")) for node in nodes]
        minindex = cpu_usage.index(min(cpu_usage))
        if nodes[minindex].is_workload_fit(workload):
            return (workload, nodes[minindex])
        else:
            return None

    def step(self, workloads: list, cluster):
        tally = []
        virtual_nodes = cluster.nodes.copy()
        # 🔹 NEW: Run dual descent for each node before scheduling

        for node in virtual_nodes.values():
            try:
                result = run_dual_descent(node)
                if result is not None:
                    print(f"[FairshareScheduler] {node.name} dual descent result:\n{result}")
            except Exception as e:
                print(f"[FairshareScheduler] Dual descent failed for {node.name}: {e}")

        # 🔹 Schedule workloads as usual
        for workload in workloads:
            planned_schedule = self.schedule(tally, workload, list(virtual_nodes.values()))
            if planned_schedule is None:
                continue
            # Update the virtual node with the new job placement
            _, virtual_node = planned_schedule
            virtual_node.place_pod(workload, cluster.current_step)

            tally.append(planned_schedule)
        return tally