FROM ubuntu:latest
RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install python3-pip -y
COPY . /app
WORKDIR /app
RUN pip3 install --no-cache-dir --upgrade pip
RUN pip3 install p2pnetwork
RUN pip3 install pycryptodome
RUN pip3 install cryptography
RUN pi3 install fastapi
EXPOSE 8231