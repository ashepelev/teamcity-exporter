FROM alpine:3.7
MAINTAINER Artem Shepelev <shepelev.artem@gmail.com>

ENV TE_LISTEN_ADDRESS=0.0.0.0
ENV TE_LISTEN_PORT=9190
ENV TE_LOG_LEVEL=INFO

RUN apk --no-cache add \
		curl \
    python2 \
    python2-dev \
    py-pip \
    bash \
    py-pip

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

ADD teamcity_exporter.py /teamcity_exporter.py

ENTRYPOINT ["/teamcity_exporter.py"]