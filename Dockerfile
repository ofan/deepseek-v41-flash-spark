# Unqualified all-in-one candidate. Never inherit the blocked production mirror.
# build-image.sh requires a separately audited sanitized runtime by tag+digest.
ARG RUNTIME_BASE
FROM ${RUNTIME_BASE}
COPY bundle/ /opt/package/
COPY scripts/entrypoint.py /opt/recipe/entrypoint.py
COPY LICENSE NOTICE /opt/recipe/
COPY licenses/ /opt/recipe/licenses/
LABEL org.opencontainers.image.source="https://github.com/ofan/deepseek-v41-flash-spark" \
      org.opencontainers.image.description="Native vision candidate; new qualification required; GLP-39 defaults ON, alpha 0.75, layers 1-39; explicit off supported"
WORKDIR /opt/package
EXPOSE 8888
ENTRYPOINT ["python3", "/opt/recipe/entrypoint.py"]
