# Packaging template, not an assertion of byte-identical production reproduction.
# RUNTIME_BASE is a release gap: supply a public, licensed, immutable ARM64
# CUDA 13 / RDMA runtime with Python3 and all binary dependencies verified.
ARG RUNTIME_BASE
FROM ${RUNTIME_BASE}
COPY bundle/ /opt/package/
COPY scripts/entrypoint.py /opt/recipe/entrypoint.py
COPY LICENSE NOTICE /opt/recipe/
COPY licenses/ /opt/recipe/licenses/
LABEL org.opencontainers.image.source="https://github.com/ofan/deepseek-v41-flash-spark"       org.opencontainers.image.revision="d04020cc1193364e042314a2ad8e0b8e6bccc46e"       org.opencontainers.image.version="2026.11.08-sampler-open-unit-r1-bundle-candidate"
WORKDIR /opt/package
EXPOSE 8888
ENTRYPOINT ["python3", "/opt/recipe/entrypoint.py"]
