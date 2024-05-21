#podman build -t build_occam:20230328 .
# Built against an old ubuntu that was a contemporary to the source
FROM ubuntu:16.04

# Run the container in our timezone so logs are easier to process
ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN true
RUN ln -sf /usr/share/zoneinfo/US/Pacific /etc/localtime

# Set up build arguments
ARG GITHUB_USERNAME
ARG GITHUB_EMAIL
ARG GITHUB_PRIVATE_KEY

RUN apt-get update
RUN apt install -y tzdata
RUN dpkg-reconfigure -f noninteractive tzdata
# We can run apache2 inside the container and start it as a service
RUN apt install -y apache2
# Maybe this can be trimmed. It was the standard suggested package list.
RUN apt install -y git gcc build-essential libgmp3-dev python-dev libxml2 libxml2-dev zlib1g-dev python-pip

RUN apt install -y libtool autoconf bison flex
RUN apt-get update && \
    apt-get install -y git vim openssh-client && \
    rm -rf /var/lib/apt/lists/*

# Set up build arguments with default values
ARG GITHUB_USERNAME=""
ARG GITHUB_EMAIL=""
ARG GITHUB_PRIVATE_KEY=""

# Configure git with the build arguments if provided
RUN if [ -n "$GITHUB_USERNAME" ] && [ -n "$GITHUB_EMAIL" ]; then \
      git config --global user.name "$GITHUB_USERNAME" && \
      git config --global user.email "$GITHUB_EMAIL"; \
    fi

# Create the .ssh directory and copy the private key if provided
RUN if [ -n "$GITHUB_PRIVATE_KEY" ]; then \
      mkdir -p /root/.ssh && \
      echo "$GITHUB_PRIVATE_KEY" > /root/.ssh/id_rsa && \
      chmod 600 /root/.ssh/id_rsa && \
      echo "Host github.com\n  IdentityFile /root/.ssh/id_rsa" > /root/.ssh/config; \
    fi

WORKDIR /var/www
# Maybe checkout something better than HEAD?
RUN git clone -b baseline https://github.com/occam-ra/occam

WORKDIR occam
# This no longer seems to work. It looks like the version of igraph-core is now invalid.
#RUN pip install python-igraph==0.7.1.post6
# Moving to igraph-0.8.0 requires some new build tools
# This command now fails -- perhaps they've been EOL'd?
#RUN apt-get update && apt-get install -y wget dpkg-dev
#RUN wget http://ports.ubuntu.com/pool/main/libs/libsigsegv/libsigsegv2_2.10-4_arm64.deb
#RUN dpkg -i libsigsegv2_2.10-4_arm64.deb
#RUN rm libsigsegv2_2.10-4_arm64.deb
#RUN wget http://ports.ubuntu.com/pool/main/m/m4/m4_1.4.17-5_arm64.deb
#RUN dpkg -i m4_1.4.17-5_arm64.deb
#RUN rm m4_1.4.17-5_arm64.deb
#RUN wget http://ports.ubuntu.com/pool/main/a/autotools-dev/autotools-dev_20150820.1_all.deb \
#    http://ports.ubuntu.com/pool/main/b/bison/libbison-dev_3.0.4.dfsg-1_arm64.deb \
#    http://ports.ubuntu.com/pool/main/f/flex/libfl-dev_2.6.0-11_arm64.deb
#RUN dpkg -i *.deb
#RUN rm *.deb
#RUN wget http://ports.ubuntu.com/pool/main/a/autoconf/autoconf_2.69-9_all.deb \
#    http://ports.ubuntu.com/pool/main/libt/libtool/libtool_2.4.6-0.1_all.deb \
#    http://ports.ubuntu.com/pool/main/b/bison/bison_3.0.4.dfsg-1_arm64.deb \
#    http://ports.ubuntu.com/pool/main/f/flex/flex_2.6.0-11_arm64.deb
#RUN dpkg -i *.deb

# Install igraph
RUN pip install python-igraph==0.8.0

RUN a2enmod cgi

RUN echo "ServerName localhost" >> /etc/apache2/apache2.conf

# Maybe put some effort into making this into a multi-stage build if keeping the container process is favored.
# Some of the libs installed above and the apache bits may be needed both in build and deploy. But for now.... complete the install in
# this build layer.

RUN make install
 
RUN chown -R www-data: /var/www/occam/install/web/data

COPY 000-default.conf /etc/apache2/sites-enabled

EXPOSE 80

CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
