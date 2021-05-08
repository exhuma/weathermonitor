FROM python:3-slim
ADD dist/weathermonitor-1.0.1-py3-none-any.whl /
RUN pip install /weathermonitor-1.0.1-py3-none-any.whl
ENTRYPOINT [ "python3", "-m", "weathermonitor" ]