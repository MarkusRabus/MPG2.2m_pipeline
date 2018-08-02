FROM alpine:3.8
MAINTAINER Markus Rabus <mrabus@astro.puc.cl>

# Environment Variables
ENV SECRET_KEY='pmzg#e2hb%!a#pb^p2a=oo=v$fdazk39v)(j5@&mk%uv6w&iar'
ENV FEROS_DATA_PATH='/home/feros_data/'

RUN apt-get update 
RUN apt-get install -y --no-install-recommends gcc
RUN apt-get install -y --no-install-recommends python
RUN apt-get install -y --no-install-recommends gfortran
RUN apt-get install -y --no-install-recommends g++
RUN apt-get install -y --no-install-recommends wget
RUN apt-get install -y --no-install-recommends nodejs 
RUN apt-get install -y --no-install-recommends swig 
RUN apt-get install -y --no-install-recommends fonts-texgyre 
RUN apt-get install -y --no-install-recommends libgsl0-dev 
RUN apt-get install -y --no-install-recommends nano 
RUN apt-get install -y --no-install-recommends git 
RUN apt-get install -y --no-install-recommends make 
RUN apt-get install -y --no-install-recommends locales
RUN apt-get install -y --no-install-recommends python-pip

## Configure default locale, see https://github.com/rocker-org/rocker/issues/19
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && locale-gen en_US.utf8 \
    && /usr/sbin/update-locale LANG=en_US.UTF-8

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8

RUN apt-get install -y --no-install-recommends r-base r-base-dev
RUN rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN mkdir /code/
RUN mkdir /code/static/
WORKDIR /code

RUN git clone git://github.com/MarkusRabus/MPG2.2m_pipeline.git

RUN pip install numpy scipy PyAstronomy
RUN pip install --no-cache-dir -r MPG2.2m_pipeline/requirements.txt

RUN ["chmod", "+x", "/code/MPG2.2m_pipeline/docker-entrypoint.sh"]
ENTRYPOINT ["/code/MPG2.2m_pipeline/docker-entrypoint.sh"]
