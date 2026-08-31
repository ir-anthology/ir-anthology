FROM python:3.14.5-trixie
ENV APP_HOME=/app
ENV DATA_PATH=${APP_HOME}/data

WORKDIR ${APP_HOME}

RUN mkdir -p ${DATA_PATH}

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./ .

RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser ${APP_HOME}
USER appuser

EXPOSE 8000

ENTRYPOINT ["fastapi", "run", "main.py"]
