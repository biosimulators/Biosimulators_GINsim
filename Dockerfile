# Base OS
FROM ghcr.io/biosimulators/biosimulators_boolnet/boolnet_base:latest

ARG VERSION="0.1.13"
ARG SIMULATOR_VERSION=2.1.5

# metadata
LABEL \
    org.opencontainers.image.authors="BioSimulators Team <info@biosimulators.org>" \
    org.opencontainers.image.vendor="BioSimulators Team" \
    \
    base_image="python:3.9-slim-buster" \
    version="${VERSION}" \
    software="BoolNet" \
    software.version="${SIMULATOR_VERSION}" \
    about.summary="Package for generation, reconstruction, simulation and analysis of synchronous, asynchronous and probabilistic Boolean networks." \
    about.home="https://sysbio.uni-ulm.de/?Software:BoolNet" \
    about.documentation="https://cran.r-project.org/web/packages/BoolNet/index.html" \
    about.license_file="https://cran.r-project.org/web/licenses/Artistic-2.0" \
    about.license="SPDX:Artistic-2.0" \
    about.tags="BioSimulators,mathematical model,logical model,simulation,systems biology,computational biology,SBML,SED-ML,COMBINE,OMEX" \
    maintainer="BioSimulators Team <info@biosimulators.org>"

# Copy code for command-line interface into image and install it
COPY . /root/Biosimulators_BoolNet
RUN pip install /root/Biosimulators_BoolNet \
    && rm -rf /root/Biosimulators_BoolNet
ENV VERBOSE=0 \
    MPLBACKEND=PDF

# Entrypoint
ENTRYPOINT ["boolnet"]
CMD []
