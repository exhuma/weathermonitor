FROM python:3-slim AS build
ADD . /src
WORKDIR /src
RUN python3 -m venv /opt/weathermonitor
RUN /opt/weathermonitor/bin/pip install -U pip
RUN /opt/weathermonitor/bin/pip install -r /src/requirements.txt
RUN /opt/weathermonitor/bin/pip install --no-deps /src

FROM python:3-slim
COPY --from=build /opt/weathermonitor /opt/weathermonitor
ENTRYPOINT [ "/opt/weathermonitor/bin/python3", "-m", "weathermonitor" ]
