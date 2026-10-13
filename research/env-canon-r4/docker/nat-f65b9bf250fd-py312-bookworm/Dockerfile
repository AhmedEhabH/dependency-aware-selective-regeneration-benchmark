# syntax=docker/dockerfile:1
# M17_D7_R4_NATIVE_IMAGE_COMPOSITION_REPAIR — R4 composite execution image
# image: envcanon/saleor-env-native-nat-f65b9bf250fd-py312-bookworm:r4-composite-20261013
# native_profile_id: nat-f65b9bf250fd  era: py312  distro: bookworm  python: 3.12
# Parent base: envcanon/saleor-env-base-py312-bookworm:latest (qualified, local)
#
# This Dockerfile replicates the EXACT frozen qualified native recipe
# (D:\wp2_env_store\dockerfiles\saleor-env-native-nat-f65b9bf250fd.Dockerfile)
# with the ONLY delta being the frozen base image swap py39 -> py312.
#   - Frozen version policy: package identities + frozen behavioral probes
#     (package-name-only, NO exact Debian version pins).
#   - D6-R1 capability providers file + libmagic1 are part of the qualified
#     recipe (required capabilities /usr/bin/file and libmagic.so.1).
#   - No task/unit special case, no dependency substitution, no network fallback.
FROM envcanon/saleor-env-base-py312-bookworm:latest AS native
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      gettext \
      libcairo2 \
      libgdk-pixbuf2.0-0 \
      liblcms2-2 \
      libopenjp2-7 \
      libpango-1.0-0 \
      libpangocairo-1.0-0 \
      libpq5 \
      libssl3 \
      libtiff6 \
      libwebp7 \
      libxml2 \
      mime-support \
      shared-mime-info \
      file \
      libmagic1 \
 && rm -rf /var/lib/apt/lists/*
# No dependency resolution here. The task/profile wheelhouse is mounted at runtime:
#   docker run --rm --network=none -v /wheelhouse/py312:/wheelhouse:ro ...