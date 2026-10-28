ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8 PYTHONUNBUFFERED=1

# Python 3 + paho-mqtt. Tenta o pacote Alpine; se faltar, usa pip.
RUN apk add --no-cache python3 \
 && ( apk add --no-cache py3-paho-mqtt \
      || ( apk add --no-cache py3-pip \
           && pip3 install --no-cache-dir --break-system-packages "paho-mqtt==1.6.1" ) )

COPY app /app

CMD [ "python3", "/app/service.py" ]
