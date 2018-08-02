FROM alpine:3.8
MAINTAINER Markus Rabus <mrabus@astro.puc.cl>

# Environment Variables
ENV SECRET_KEY='pmzg#e2hb%!a#pb^p2a=oo=v$fdazk39v)(j5@&mk%uv6w&iar'
ENV FEROS_DATA_PATH='/home/feros_data/'

RUN apk update
RUN apk add --no-cache gcc g++ gfortran make wget gsl sshfs nano

RUN apk add --no-cache python \
    python-dev \
    py-pip

RUN apk add --no-cache swig
RUN apk add --no-cache git
RUN apk add --no-cache rsync libffi-dev
RUN apk add --no-cache freetype-dev openblas-dev #lapack-dev
RUN apk add --no-cache gsl-dev

# R runtime dependencies
RUN apk --no-cache add \
        readline-dev \
        icu-dev \
        bzip2-dev \
        xz-dev \
        pcre-dev \
        libjpeg-turbo-dev \
        libpng-dev \
        tiff-dev  \
        curl-dev \
        zip \
        file \
        coreutils \
        bash && \
# R build dependencies
    apk --no-cache add --virtual build-deps \
        curl \
        perl \
        openjdk8-jre-base \
        pango-dev \
        cairo-dev \
        tcl-dev \
        tk-dev && \
    cd /tmp && \
# Download source code
    curl -O https://cran.r-project.org/src/base/R-3/R-3.5.1.tar.gz && \
# Extract source code
    tar -xf R-3.5.1.tar.gz && \
    cd R-3.5.1 && \
# Sect compiler flags
    CFLAGS="-g -O2 -fstack-protector-strong -D_DEFAULT_SOURCE -D__USE_MISC" \
    CXXFLAGS="-g -O2 -fstack-protector-strong -D_FORTIFY_SOURCE=2 -D__MUSL__" \
# configure script options
    ./configure --prefix=/usr \
                --sysconfdir=/etc/R \
                --localstatedir=/var \
                rdocdir=/usr/share/doc/R \
                rincludedir=/usr/include/R \
                rsharedir=/usr/share/R \
                --enable-memory-profiling \
                --enable-R-shlib \
                --disable-nls \
                --without-x \
                --without-recommended-packages && \
# Build and install R
    make && \
    make install && \
    cd src/nmath/standalone && \
    make && \
    make install && \
# Remove build dependencies
    apk del --purge --rdepends build-deps && \
    rm -f /usr/lib/R/bin/R && \
    ln -s /usr/bin/R /usr/lib/R/bin/R && \
# Fis library path
    echo "R_LIBS_SITE=\${R_LIBS_SITE-'/usr/local/lib/R/site-library:/usr/lib/R/library'}" >> /usr/lib/R/etc/Renviron && \
# Add default CRAN mirror
    echo 'options(repos = c(CRAN = "https://cloud.r-project.org/"))' >> /usr/lib/R/etc/Rprofile.site && \
# Add symlinks for the config ifile in /etc/R
    mkdir -p /etc/R && \
    ln -s /usr/lib/R/etc/* /etc/R/ && \
# Add library directory
    mkdir -p /usr/local/lib/R/site-library && \
    chgrp users /usr/local/lib/R/site-library && \
# Clean up
    rm -rf /usr/lib/R/library/translations && \
    rm -rf /tmp/*

RUN ln -s /usr/include/locale.h /usr/include/xlocale.h

RUN pip install --upgrade pip

RUN pip install numpy scipy PyAstronomy

RUN mkdir /code/
RUN mkdir /code/static/
WORKDIR /code

RUN git clone git://github.com/MarkusRabus/MPG2.2m_pipeline.git

RUN pip install --no-cache-dir -r MPG2.2m_pipeline/requirements.txt &&\
cd MPG2.2m_pipeline/ceres && \
python install.py

RUN ["chmod", "+x", "/code/MPG2.2m_pipeline/docker-entrypoint.sh"]
ENTRYPOINT ["/code/MPG2.2m_pipeline/docker-entrypoint.sh"]
