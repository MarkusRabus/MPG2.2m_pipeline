FROM debian:wheezy
MAINTAINER Markus Rabus <mrabus@astro.puc.cl>


# Environment Variables
ENV SECRET_KEY='pmzg#e2hb%!a#pb^p2a=oo=v$fdazk39v)(j5@&mk%uv6w&iar'
ENV FEROS_DATA_PATH='/home/feros_data/'
ENV STATIC_STORAGE whitenoise.storage.CompressedManifestStaticFilesStorage
ENV PYTHONPATH "${PYTHONPATH}:/code/"
ENV FEROS_DATA_PATH='/data/'
ENV DIRECTORY_TO_WATCH='/original_data/'

# ensure local python is preferred over distribution python
ENV PATH /usr/local/bin:$PATH
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN apt-get update && \
    apt-get install -y gcc-4.4 \
    gfortran-4.4 \
    g++-4.4 \
    make \ 
    wget

RUN ln -s /usr/bin/gcc-4.4 /usr/bin/gcc && \
    ln -s /usr/bin/gfortran-4.4 /usr/bin/gfortran && \
    ln -s /usr/bin/cpp-4.4 /usr/bin/cpp && \
    ln -s /usr/bin/g++-4.4 /usr/bin/g++


RUN apt-get install -y ca-certificates \
    libreadline-gplv2-dev \
    libncursesw5-dev \
    libssl-dev \
    libsqlite3-dev \
    tk-dev \
    libgdbm-dev \
    libc6-dev \
    libbz2-dev

RUN wget https://www.python.org/ftp/python/2.7.13/Python-2.7.13.tgz && \
    tar -xzf Python-2.7.13.tgz -C /usr/src  && \
    cd /usr/src/Python-2.7.13 && \
    ./configure && \
    make && \
    make altinstall

RUN ln -s /usr/local/bin/python2.7 /usr/local/bin/python

RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python get-pip.py

RUN apt-get install --no-install-recommends -y libgsl0-dev 
RUN apt-get install --no-install-recommends -y nano
RUN apt-get install --no-install-recommends -y git
RUN apt-get install --no-install-recommends -y swig
RUN apt-get install --no-install-recommends -y curl
RUN apt-get install --no-install-recommends -y zip unzip
RUN apt-get install --no-install-recommends -y libopenblas-dev
RUN apt-get install --no-install-recommends -y r-base
RUN apt-get install --no-install-recommends -y libffi-dev libssl-dev

# Need to do this outside of requirements.txt, needed for packages in requirements.txt
RUN pip install --no-cache-dir numpy
RUN pip install --no-cache-dir scipy
RUN pip install --no-cache-dir matplotlib

RUN mkdir /srv/logs/

RUN mkdir /code/
RUN mkdir /code/static/
WORKDIR /code

RUN git clone git://github.com/MarkusRabus/MPG2.2m_pipeline.git

RUN pip install --no-cache-dir -r MPG2.2m_pipeline/requirements.txt

RUN git clone git://github.com/statsmodels/statsmodels.git
RUN cd statsmodels && \
    python setup.py install

RUN apt-get install --no-install-recommends -y python-dev
RUN rm -rf /var/lib/apt/lists/*

RUN ["chmod", "+x", "/code/MPG2.2m_pipeline/docker-entrypoint.sh"]
ENTRYPOINT ["/code/MPG2.2m_pipeline/docker-entrypoint.sh"]
