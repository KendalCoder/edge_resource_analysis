import math

from ..cluster_utils import convert_to_millicores, convert_to_bytes

class XavierNX:
	def __init__(self, node_template):
		self.name = node_template["metadata"]["name"]
		self.labels = node_template["metadata"]["labels"]
		self.metrics = {}
		self.pods = {}
		self.capacity_cpu = convert_to_millicores(node_template["status"]["capacity"]["cpu"])
		self.count_finished_pod = 0

		# Power consumption in watts based on application's CPU usage.
		# The system is assumed to be idle at 5W.
		self.powerlist = list(range(5, 16))

	def __str__(self):
		return self.name

	def estimate_power(self, cpu_usage:int):
		index = math.floor(cpu_usage / 10)
		if index >= len(self.powerlist):
			return self.powerlist[-1]
		left = self.powerlist[index]
		right = self.powerlist[index + 1 if cpu_usage%10 != 0 else index]
		alpha = (cpu_usage / 10) - index
		return alpha * right + (1 - alpha) * left
	
	def get_node_metrics(self):
		return self.metrics.update({
			"finished_workloads", self.count_finished_pod,
			"running_workloads", len(self.pods),
		}).items()
	
	def place_pod(self, pod, step):
		pod.start_at(step)
		self.pods[pod.name] = pod
	
	def update(self, step, events: list):
		finished_pods = []
		# Cumulated CPU and memory usage of all pods running on this node.
		cumulated_cpu = 0
		cumulated_memory = 0
		for pod_name in self.pods.keys():
			pod = self.pods.pop(pod)
			cumulated_cpu += pod.request_cpu
			cumulated_memory += pod.request_memory

			if pod.ended <= step:
				finished_pods.append(pod)
				self.count_finished_pod += 1
			else:
				self.pods[pod_name] = pod

		self.metrics["cpu"] = cumulated_cpu
		self.metrics["memory"] = cumulated_memory

		# Power consumption in watts, estimated based on application's CPU usage.
		cpu_usage = round(cumulated_cpu / self.capacity_cpu * 100)
		self.metrics["power"] = self.estimate_power(cpu_usage)

		return finished_pods