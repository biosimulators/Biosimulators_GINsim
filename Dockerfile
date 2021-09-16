# Base OS
FROM python:3.9-slim-buster

ARG VERSION="0.0.7"
ARG SIMULATOR_VERSION=3.0.0b

# metadata
LABEL \
    org.opencontainers.image.title="GINsim" \
    org.opencontainers.image.version="${SIMULATOR_VERSION}" \
    org.opencontainers.image.description="Tool for modeling and simulating genetic regulatory networks." \
    org.opencontainers.image.url="http://ginsim.org/" \
    org.opencontainers.image.documentation="http://doc.ginsim.org/" \
    org.opencontainers.image.authors="BioSimulators Team <info@biosimulators.org>" \
    org.opencontainers.image.vendor="BioSimulators Team" \
    org.opencontainers.image.licenses="SPDX:GPL-3.0-only" \
    \
    base_image="python:3.9-slim-buster" \
    version="${VERSION}" \
    software="GINsim" \
    software.version="${SIMULATOR_VERSION}" \
    about.summary="Tool for modeling and simulating genetic regulatory networks." \
    about.home="http://ginsim.org/" \
    about.documentation="http://doc.ginsim.org/" \
    about.license_file="http://choosealicense.com/licenses/gpl-3.0/" \
    about.license="SPDX:GPL-3.0-only" \
    about.tags="BioSimulators,mathematical model,logical model,simulation,systems biology,computational biology,SBML,SED-ML,COMBINE,OMEX" \
    maintainer="BioSimulators Team <info@biosimulators.org>"

# fonts for matplotlib
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

# Install GINsim
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        default-jre \
        wget \
    \
    && cd /tmp \
    && pip install ginsim \
    && wget https://raw.githubusercontent.com/GINsim/GINsim-python/master/ginsim_setup.py \
    && python ginsim_setup.py \
    \
    && rm ginsim_setup.py \
    && apt-get remove -y \
        wget \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy code for command-line interface into image and install it
COPY . /root/Biosimulators_GINsim
RUN pip install /root/Biosimulators_GINsim \
    && rm -rf /root/Biosimulators_GINsim
RUN mkdir -p /.config/matplotlib \
    && mkdir -p /.cache/matplotlib \
    && chmod ugo+rw /.config/matplotlib \
    && chmod ugo+rw /.cache/matplotlib \
    && python -c "import matplotlib.font_manager"
ENV VERBOSE=0 \
    MPLBACKEND=PDF

# Entrypoint
ENTRYPOINT ["biosimulators-ginsim"]
CMD []
