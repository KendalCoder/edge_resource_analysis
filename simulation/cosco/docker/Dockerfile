FROM python:3.8

RUN apt-get update \
  && apt-get install -y \
  python3-pip \
  nano \
  git \
  wget \
  curl

RUN pip3 install -U pip setuptools

WORKDIR /workspace
RUN git clone https://github.com/imperial-qore/COSCO.git /workspace/COSCO
RUN cd COSCO \
  && pip3 install matplotlib scikit-learn \
  && pip3 install -r requirements.txt \
  && pip3 install torch==1.7.1+cpu torchvision==0.8.2+cpu -f https://download.pytorch.org/whl/torch_stable.html

COPY idling.sh /app/
ENTRYPOINT ["/bin/bash", "/app/idling.sh"]