#!/bin/bash

KWOK_VERSION=$(kwokctl --version | cut -d ' ' -f 3)
echo "KWOK version is $KWOK_VERSION"

echo "Downloading metrics usage..."
wget -O /tmp/metrics-usage.yaml https://github.com/kubernetes-sigs/kwok/releases/download/$KWOK_VERSION/metrics-usage.yaml

echo "Launching a cluster with metrics server enabled..."
kwokctl create cluster \
  --name mycluster \
  --enable-metrics-server \
  -c /tmp/metrics-usage.yaml \
  --enable-crds=Metric \
  --enable-crds=ClusterResourceUsage \
  --enable-crds=ResourceUsage

echo "Adding CRDs..."
# The -c /tmp/metrics-usage.yaml does not seem to work in v0.6.1
# so we apply it manually.
kubectl apply -f /tmp/metrics-usage.yaml

wget -O /tmp/kwok_crds.yaml https://github.com/kubernetes-sigs/kwok/releases/download/$KWOK_VERSION/kwok.yaml
kubectl apply -f /tmp/kwok_crds.yaml