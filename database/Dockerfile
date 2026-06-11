FROM adfreiburg/qlever
ARG APP_HOME=/app
ENV APP_HOME=${APP_HOME}
ENV DATA_PATH=${APP_HOME}/data

WORKDIR ${APP_HOME}

RUN mkdir -p ${DATA_PATH}

COPY ./ .

EXPOSE 7016

COPY --chmod=777 run_qlever.sh .

ENTRYPOINT ["./run_qlever.sh"]
