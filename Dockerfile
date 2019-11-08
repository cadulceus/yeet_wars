FROM python:2.7

WORKDIR /opt
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY ./ ./

RUN pip install .
ENV YEET_CONFIG_FILE csaw_config.json

EXPOSE 5000
CMD python server/server.py
