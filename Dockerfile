FROM centos:centos7
MAINTAINER Markus Rabus <mrabus@astro.puc.cl>

# Environment Variables
ENV SECRET_KEY='pmzg#e2hb%!a#pb^p2a=oo=v$fdazk39v)(j5@&mk%uv6w&iar'
ENV FEROS_DATA_PATH='/home/feros_data/'
ENV STATIC_STORAGE whitenoise.storage.CompressedManifestStaticFilesStorage
ENV PYTHONPATH "${PYTHONPATH}:/code/"
ENV FEROS_DATA_PATH='/data/'
ENV DIRECTORY_TO_WATCH='/original_data/'


RUN yum -y update; yum clean all
RUN yum install -y epel-release; yum clean all 
RUN yum install -y gcc gcc-c++ gcc-gfortran make wget gsl.x86_64 gsl-devel sshfs nano; yum clean all
RUN yum install -y swig; yum clean all
RUN yum install -y r-base r-base-dev; yum clean all
RUN yum install -y git; yum clean all
RUN yum install -y tkinter; yum clean all
RUN yum install -y rsync; yum clean all
RUN yum install -y python-pip; yum clean all
RUN yum install -y python2-devel; yum clean all

RUN pip install --upgrade pip

RUN pip install numpy scipy PyAstronomy

RUN mkdir /code/
RUN mkdir /code/static/
WORKDIR /code
RUN git clone git://github.com/MarkusRabus/MPG2.2m_pipeline.git 

RUN pip install --no-cache-dir -r MPG2.2m_pipeline/requirements.txt

ENTRYPOINT ["/code/MPG2.2m_pipeline/docker-entrypoint.sh"]
