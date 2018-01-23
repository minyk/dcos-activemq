FROM centos:7.3.1611

RUN yum install -y unzip tar && mkdir -p /usr/share/dcos

COPY *.zip /usr/local/dcos/
COPY *.tar.gz /usr/local/dcos/
COPY entrypoint.sh /entrypoint.sh

ENV JAVA_URI http://api.activemq.marathon.l4lb.thisdcos.directory/v1/files/jre-8u152-linux-x64.tar.gz
ENV LIBMESOS_URI http://api.activemq.marathon.l4lb.thisdcos.directory/v1/files/libmesos-bundle-master-28f8827.tar.gz
ENV EXECUTOR_URI http://api.activemq.marathon.l4lb.thisdcos.directory/v1/files/executor.zip
ENV BOOTSTRAP_URI http://api.activemq.marathon.l4lb.thisdcos.directory/v1/files/bootstrap.zip

ENTRYPOINT ["/entrypoint.sh"]
