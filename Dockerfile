FROM ubuntu:17.10
SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y python3-pip

COPY requirements.txt /tmp
RUN pip3 install --upgrade -r /tmp/requirements.txt
RUN rm /tmp/requirements.txt

COPY . /app
WORKDIR /app



ENV GROUPME_TOKEN "9f6dd8f0e53e0135af1949eb4576364f"
ENV MONGO_PASS "whiskyM1"
ENV MONGO_USER "mongoUser"

CMD ["python3", "app.py"]

