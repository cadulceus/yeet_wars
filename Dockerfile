FROM python:3.10

WORKDIR /opt
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY ./ ./

RUN pip install .
ENV YEET_CONFIG_FILE block_config.json

EXPOSE 5000
CMD python3 server/server.py
