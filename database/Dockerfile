FROM adfreiburg/qlever
WORKDIR /app

COPY Qleverfile .
COPY add_authors_from_stream.rq .
COPY add_editors_from_stream.rq .
COPY add_publications_from_stream.rq .
COPY add_signatures_from_stream.rq .
COPY add_stream.rq .
COPY add_workshop_stream.rq .
COPY streams.txt .
COPY workshop_streams.txt .
COPY get_data.sh .

EXPOSE 7016

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

COPY --chmod=777 <<EOF run.sh
#!/usr/bin/env sh
set -e
qlever get-data
qlever index
exec qlever-server -i test -j 8 -p 7016 -m 10G -c 5G -e 1G -k 200 -s 30s -a test9F8xXCrV5J1g
EOF

#RUN ./run.sh

#ENTRYPOINT ["bash"]
ENTRYPOINT ["./run.sh"]
