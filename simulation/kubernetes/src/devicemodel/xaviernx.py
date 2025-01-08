import math

from ..utils import *

class XavierNX:
	def __init__(self, kube_node, kube_client):
		self.name = kube_node["metadata"]["name"]
		self.labels = kube_node["metadata"]["labels"]
		self.kube_client = kube_client
		self.metrics = {}

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
		return self.metrics.items()
	
	def update(self):
		# Cumulated CPU and memory usage of all pods running on this node.
		cumulated_cpu = 0
		cumulated_memory = 0
		for pod in self.kube_client.get_pods_on_node(self.name).items:
			if pod.status.phase != "Running":
				continue # Skip those pods that are not running

			cumulated_cpu += convert_to_millicores(pod.spec.containers[0].resources.requests["cpu"])
			cumulated_memory += convert_to_bytes(pod.spec.containers[0].resources.requests["memory"])
		self.metrics["cpu"] = cumulated_cpu
		self.metrics["memory"] = cumulated_memory

		# Power consumption in watts, estimated based on application's CPU usage.
		node = self.kube_client.get_node(self.name)
		node_cpu_capacity = convert_to_millicores(node.status.capacity["cpu"])
		cpu_usage = round(cumulated_cpu / node_cpu_capacity * 100)
		self.metrics["power"] = self.estimate_power(cpu_usage)