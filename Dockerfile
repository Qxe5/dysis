FROM python:3-alpine

WORKDIR /dysis/

ARG tmp='gcc musl-dev git'

RUN apk add $tmp --no-cache && \
    git clone https://github.com/Qxe5/dysis.git . && \
    python -m pip install -r requirements.txt --no-cache-dir && \
    apk del $tmp

ENTRYPOINT python bot.py
