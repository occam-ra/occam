#podman build -t build_occam:20230328 .
# Built against an old ubuntu that was a contemporary to the source
FROM ubuntu:16.04

# Run the container in our timezone so logs are easier to process
ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN true
RUN ln -sf /usr/share/zoneinfo/US/Pacific /etc/localtime

RUN apt-get update
RUN apt install -y tzdata
RUN dpkg-reconfigure -f noninteractive tzdata
# We can run apache2 inside the container and start it as a service
RUN apt install -y apache2
# Maybe this can be trimmed. It was the standard suggested package list.
RUN apt install -y git gcc build-essential libgmp3-dev python-dev libxml2 libxml2-dev zlib1g-dev python-pip
RUN apt install -y libtool autoconf bison flex
RUN apt install -y git vim openssh-client
RUN apt install -y libboost-math-dev
# Set up build arguments with default values
ARG GITHUB_USERNAME
ARG GITHUB_EMAIL
ARG GITHUB_PRIVATE_KEY

WORKDIR /var/www

# Maybe checkout something better than HEAD?
RUN git clone https://github.com/occam-ra/occam.git

WORKDIR occam

# Configure git with the build arguments if provided
RUN if [ -n "$GITHUB_USERNAME" ] && [ -n "$GITHUB_EMAIL" ]; then \
      git config --global user.name "$GITHUB_USERNAME" && \
      git config --global user.email "$GITHUB_EMAIL" && \
      git remote set-url origin git@github.com:occam-ra/occam.git; \
    fi

# Create the .ssh directory and copy the private key if provided
RUN if [ -n "$GITHUB_PRIVATE_KEY" ]; then \
      mkdir -p /root/.ssh && \
      echo "$GITHUB_PRIVATE_KEY" > /root/.ssh/id_github && \
      chmod 600 /root/.ssh/id_github && \
      echo "Host github.com\n  IdentityFile /root/.ssh/id_github" > /root/.ssh/config; \
    fi

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
