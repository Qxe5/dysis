FROM python:3-alpine

WORKDIR /dysis/

RUN apk add git --no-cache && \
    git clone https://github.com/Qxe5/dysis.git . && \
    python -m pip install -r requirements.txt --no-cache-dir

ENTRYPOINT python bot.py
