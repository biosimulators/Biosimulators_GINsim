# Base OS
FROM python:3.9-slim-buster

ARG VERSION="0.0.1"
ARG SIMULATOR_VERSION=3.0.0b

# metadata
LABEL \
    org.opencontainers.image.authors="BioSimulators Team <info@biosimulators.org>" \
    org.opencontainers.image.vendor="BioSimulators Team" \
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

# Install GINsim
RUN mkdir /usr/share/man/man1/ \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends \
        default-jre-headless \
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
ENV PATH=/usr/local/share/colomoto/bin:$PATH

# Copy code for command-line interface into image and install it
COPY . /root/Biosimulators_GINsim
RUN pip install /root/Biosimulators_GINsim \
    && rm -rf /root/Biosimulators_GINsim
ENV VERBOSE=0 \
    MPLBACKEND=PDF

# Entrypoint
ENTRYPOINT ["biosimulators-ginsim"]
CMD []
