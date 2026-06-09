FROM python:3.14.5-trixie
WORKDIR /app

COPY main.py .
COPY sparqlTemplates.py .

RUN pip install "fastapi[standard]"

EXPOSE 8000

#ARG UID=10001
#RUN adduser \
#    --disabled-password \
#    --gecos "" \
#    --home "/nonexistent" \
#    --shell "/sbin/nologin" \
#    --no-create-home \
#    --uid "${UID}" \
#    appuser
#USER appuser

#COPY --chmod=777 <<EOF run.sh
#!/usr/bin/env sh
#set -e
#qlever get-data
#qlever index
#exec qlever-server -i test -j 8 -p 7016 -m 10G -c 5G -e 1G -k 200 -s 30s -a test9F8xXCrV5J1g
#EOF

#RUN ./run.sh

#ENTRYPOINT ["bash"]
ENTRYPOINT ["fastapi", "run", "main.py"]
