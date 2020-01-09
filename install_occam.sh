#!/bin/bash

# Update apt
sudo apt update
sudo apt upgrade

# Install dependencies
sudo apt install -y apache2
sudo apt install -y python2.7 python-pip
sudo apt install -y gcc build-essential libgmp3-dev python-dev libxml2 libxml2-dev zlib1g-dev

# Make OCCAM
make install

# Setup Apache
sudo a2enmod cgi
echo <<EOT >> /etc/apache2/sites-enabled/000-default.conf
<VirtualHost *:80>
	# The ServerName directive sets the request scheme, hostname and port that
	# the server uses to identify itself. This is used when creating
	# redirection URLs. In the context of virtual hosts, the ServerName
	# specifies what hostname must appear in the request's Host: header to
	# match this virtual host. For the default virtual host (this file) this
	# value is not decisive as it is used as a last resort host regardless.
	# However, you must set it for any further virtual host explicitly.
	#ServerName www.example.com

	ServerAdmin webmaster@localhost
	DocumentRoot /home/occam/occam/install/web

	# Available loglevels: trace8, ..., trace1, debug, info, notice, warn,
	# error, crit, alert, emerg.
	# It is also possible to configure the loglevel for particular
	# modules, e.g.
	#LogLevel info ssl:warn

	ErrorLog ${APACHE_LOG_DIR}/error.log
	CustomLog ${APACHE_LOG_DIR}/access.log combined

	# For most configuration files from conf-available/, which are
	# enabled or disabled at a global level, it is possible to
	# include a line for only one particular virtual host. For example the
	# following line enables the CGI configuration for this host only
	# after it has been globally disabled with "a2disconf".
	#Include conf-available/serve-cgi-bin.conf
	<Directory /home/occam/occam/install/web>
		Options +ExecCGI
		AddHandler cgi-script .cgi .pl
		options Indexes FollowSymLinks
		AllowOverride All
		Require all granted
	</Directory>
</VirtualHost>

# vim: syntax=apache ts=4 sw=4 sts=4 sr noet
EOT

# TODO Change /etc/apache2/envvars

# Set Permissions
chown -R www-data install/web/
chgrp -R www-data install/web/
chmod -R 750 install/web/
chmod g+s install/web/
chmod g+w install/web/data/

# 
