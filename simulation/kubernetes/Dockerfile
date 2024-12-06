FROM python:3.10

RUN apt-get update \
  && apt-get install -y \
  curl \
  wget \
  nano \
  python3-pip

ENV KWOK_REPO=kubernetes-sigs/kwok
ENV KWOK_VERSION=v0.6.1
ENV OS=linux
ENV ARCH=amd64
ADD "https://github.com/${KWOK_REPO}/releases/download/${KWOK_VERSION}/kwokctl-${OS}-${ARCH}" /usr/local/bin/kwokctl
ADD "https://github.com/${KWOK_REPO}/releases/download/${KWOK_VERSION}/kwok-${OS}-${ARCH}" /usr/local/bin/kwok
ENV KUBECTL_VERSION=v1.31.3
ADD "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" /usr/local/bin/kubectl
RUN chmod +x /usr/local/bin/kwokctl \
  /usr/local/bin/kwok \
  /usr/local/bin/kubectl \
  && ln /usr/local/bin/kubectl /usr/local/bin/k

COPY setup.sh create requirements.txt /app/
RUN pip3 install -U pip \
  && pip3 install -r /app/requirements.txt

COPY template /app/template