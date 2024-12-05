import time
import json
import random

from kubernetes import client, config, watch

config.load_kube_config()
v1=client.CoreV1Api()

scheduler_name = "myscheduler"

def nodes_available():
    ready_nodes = []
    for n in v1.list_node().items:
            for status in n.status.conditions:
                if status.status == "True" and status.type == "Ready":
                    ready_nodes.append(n.metadata.name)
    return ready_nodes


def scheduler(name, node, namespace="default"):
    target=client.V1ObjectReference()
    target.kind="Node"
    target.apiVersion="v1"
    target.name= node
    
    meta=client.V1ObjectMeta()
    meta.name=name
    body=client.V1Binding(target=target)
    body.metadata=meta
    
    # In the Kubernetes Python client, it is known that
    # the below operation raises an exception even though
    # it succeeds the operation. For more information, see
    # https://github.com/kubernetes-client/python/issues/547
    try:
        res = v1.create_namespaced_binding(namespace, body)
    except:
        pass
    return True


def main():
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, "default"):
        if event['object'].status.phase == "Pending" and event['object'].spec.scheduler_name == scheduler_name:
            try:
                res = scheduler(event['object'].metadata.name, random.choice(nodes_available()))
                print(res)
            except client.rest.ApiException as e:
                print(json.loads(e.body)['message'])
                    
if __name__ == '__main__':
    main()