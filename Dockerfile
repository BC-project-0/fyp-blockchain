FROM ubuntu:20.04
RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install python3-pip -y
COPY . /app
WORKDIR /app
RUN pip3 install --no-cache-dir --upgrade pip
RUN pip3 install -r requirements.txt
# VOLUME /app/data
EXPOSE 8231
EXPOSE 80
ENTRYPOINT [ "python3", "nodev2.py" ]