FROM python:3-slim
ARG DISTFILE
ADD dist/${DISTFILE} /
RUN pip install /${DISTFILE}
ENTRYPOINT [ "python3", "-m", "weathermonitor" ]
