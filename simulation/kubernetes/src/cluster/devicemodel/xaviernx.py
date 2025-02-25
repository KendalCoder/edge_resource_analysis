import math

from ..cluster_utils import convert_to_millicores, convert_to_bytes

class XavierNX:
	def __init__(self, node_template):
		self.name = node_template["metadata"]["name"]
		self.labels = node_template["metadata"]["labels"]
		self.metrics = {}
		self.pods = {}
		self.capacity_cpu = convert_to_millicores(node_template["status"]["capacity"]["cpu"])
		self.capacity_memory = convert_to_bytes(node_template["status"]["capacity"]["memory"])
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
		self.metrics.update({
			"finished_workloads": self.count_finished_pod,
			"running_workloads": len(self.pods.keys()),
		})
		return self.metrics.items()
	
	def place_pod(self, pod, step):
		pod.start_at(step)
		self.pods[pod.name] = pod

		# Update the resource usage of the node
		self.calculate_resource_usage()

	def has_gpu(self):
		return self.labels.get("waggle.io/resource.gpu", False)
	
	def get_label(self, label_name):
		name_with_prefix = f"waggle.io/{label_name}"
		return self.labels.get(name_with_prefix, None)

	def is_workload_fit(self, workload):
		""" Check if the workload can be placed on the node.
		"""
		cpu_usage = 0
		memory_usage = 0
		for _, pod in self.pods.items():
			cpu_usage += pod.request_cpu
			memory_usage += pod.request_memory
		return (workload.request_cpu + cpu_usage) < self.capacity_cpu and \
			(workload.request_memory + memory_usage) < self.capacity_memory
	
	def calculate_resource_usage(self):
		cumulated_cpu = 0
		cumulated_memory = 0
		for pod in list(self.pods.values()):
			cumulated_cpu += pod.request_cpu
			cumulated_memory += pod.request_memory
		self.metrics["cpu"] = cumulated_cpu
		self.metrics["memory"] = cumulated_memory

		# Power consumption in watts, estimated based on application's CPU usage.
		cpu_usage = round(cumulated_cpu / self.capacity_cpu * 100)
		self.metrics["power"] = self.estimate_power(cpu_usage)

	def update(self, step, events: list):
		finished_pods = []
		for pod_name in list(self.pods.keys()):
			pod = self.pods.pop(pod_name)

			if pod.ended <= step:
				finished_pods.append(pod)
				self.count_finished_pod += 1
			else:
				self.pods[pod_name] = pod

		# Update the resource usage of the node
		self.calculate_resource_usage()
		return finished_pods