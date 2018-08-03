FROM debian:wheezy
MAINTAINER Markus Rabus <mrabus@astro.puc.cl>

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH

#RUN echo "deb http://packages.debian.org/wheezy/gcc-4.4" >> /etc/apt/sources.list

RUN apt-get update --fix-missing && apt-get install -y gcc-4.4 gfortran-4.4 g++-4.4 make wget  \
    libglib2.0-0 libxext6 libsm6 libxrender1 libgsl0-dev bzip2 ca-certificates nano git swig zip

RUN rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/gcc-4.4 /usr/bin/gcc && \
    ln -s /usr/bin/gfortran-4.4 /usr/bin/gfortran && \
    ln -s /usr/bin/cpp-4.4 /usr/bin/cpp && \
    ln -s /usr/bin/g++-4.4 /usr/bin/g++

RUN mkdir /code/
RUN mkdir /code/static/
WORKDIR /code

RUN git clone git://github.com/MarkusRabus/MPG2.2m_pipeline.git

RUN wget --quiet https://repo.anaconda.com/archive/Anaconda2-4.3.0-Linux-x86_64.sh -O ~/anaconda.sh && \
    /bin/bash ~/anaconda.sh -b -p /opt/conda && \
    rm ~/anaconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

RUN conda install numpy
RUN conda install scipy
RUN conda install matplotlib
RUN conda install -c r rpy2 
RUN conda install pycurl
RUN conda install ephem
RUN conda install libgfortran==1

RUN cd MPG2.2m_pipeline && \
    tar xvf PyAstronomy-0.8.1.tar && \
    unzip PyFITS.zip && \
    cd PyAstronomy-0.8.1 && \
    python setup.py install && \
    cd ../PyFITS-master && \
    python setup.py install 

RUN conda install -c statsmodels statsmodels 
RUN conda install numpy

RUN ["chmod", "+x", "/code/MPG2.2m_pipeline/docker-entrypoint.sh"]
ENTRYPOINT ["/code/MPG2.2m_pipeline/docker-entrypoint.sh"]
