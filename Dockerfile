FROM python:3.6-alpine

RUN apk update && apk --no-cache add gcc 

RUN pip install cython

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

RUN python3 -m venv /usr/src/venv
ENV VIRTUAL_ENV="/usr/src/venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY . /usr/src/app

RUN pip install -r requirements.txt

ENV PYTHONPATH="/usr/src/app"

EXPOSE 8089
CMD  ["locust -f iot-publish.py -H localhost:1883"]
