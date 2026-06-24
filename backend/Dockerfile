FROM python:3.14.5-trixie
ENV APP_HOME=/app
ENV DATA_PATH=${APP_HOME}/data

WORKDIR ${APP_HOME}

RUN mkdir -p ${DATA_PATH}

COPY ./ .

RUN pip install "fastapi[standard]" "PyJWT" "cryptography"

EXPOSE 8000

ENTRYPOINT ["fastapi", "run", "main.py"]
