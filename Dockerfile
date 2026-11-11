# New all-in-one candidate, NOT the byte-identical production mirror.
# The qualified runtime is the exact private image; transfer currently blocked.
ARG RUNTIME_BASE=ghcr.io/ofan/deepseek-v41-flash-spark:2026.11.08-native-vision-trial-r1@sha256:edb2bd48c5c146bd33c588bc8fcd0c79d3c3daf9b9084b69c6106ae345fd5fc9
FROM ${RUNTIME_BASE}
COPY bundle/ /opt/package/
COPY scripts/entrypoint.py /opt/recipe/entrypoint.py
COPY LICENSE NOTICE /opt/recipe/
COPY licenses/ /opt/recipe/licenses/
LABEL org.opencontainers.image.source="https://github.com/ofan/deepseek-v41-flash-spark" \
      org.opencontainers.image.revision="b7c3eb5b12a030725bfb0186d27065bc6e376685" \
      org.opencontainers.image.version="2026.11.08-native-vision-bundle-candidate"
WORKDIR /opt/package
EXPOSE 8888
ENTRYPOINT ["python3", "/opt/recipe/entrypoint.py"]
