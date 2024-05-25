# Installation

## Overview

The current version of OCCAM runs on a Linux webserver. The installation procedure is fairly well defined for Linux, so you should be able to get OCCAM up and running on your Linux system.

It is possible that you may be able to install OCCAM locally on a dedicated machine. This is not recommended, as it is difficult and error prone.  If you choose this approach, the instructions in [`VIRTUALENV.md`](VIRTUALENV.md) may be helpful. Then skip to installing OCCAM below.

For most users, the recommended installation method at this time is to use VirtualBox, which will let you create a fully containerized linux machine inside your existing OS. This will isolate OCCAM inside the VirtualBox and not require configuration changes to your larger system. The procedure is as follows:

1. Install a virtual machine or virtual environment, and install Ubuntu or some other Linux server on your (virtual) machine, and install dependencies
2. Install OCCAM using git
3. Install apache and configure it for CGI-bin
4. Set file ownership and permissions to allow apache to access the files

So let's begin:

## Ready A Virtual Machine

In this section we show how to set up a VirtualBox virtual machine running Ubuntu 16.04, ready to build OCCAM. Note that other VM options are available and viable.

### Install VirtualBox

To create an instance of OCCAM without a dedicated Linux machine you can [Download VirtualBox](https://www.virtualbox.org/wiki/Downloads).  Select New and make sure it is of the Linux type with enough memory and storage space to run the chosen OS.

You'll want to make sure your box is "Attached to" a Bridged Adapter in Network settings for Adapter 1. The rest of the settings are based mostly on the preference of the user and limitations of the host machine.

You can then create a Linux server box by installing from a [Ubuntu 16.04 LTS ISO](http://releases.ubuntu.com/16.04/).

### Install Ubuntu Server 16.04

You will need Ubuntu 16.04 LTS to run OCCAM, as later versions of Ubuntu will most likely not support Python 2.7.

Choose the Ubuntu Server for either 32-bit or 64-bit (depending on the host OS) from [ISOs](http://releases.ubuntu.com/16.04/).

Configure VirtualBox to use this ISO. Note that the ISO will need to be available in the same location for the entire VirtualBox setup phase.

Use at least 2GB of memory and 5GB of storage.

### Update Installation

You will want to make sure you are at current installation, including security fixes.

```
$ sudo apt update
$ sudo apt upgrade
```

### Install OpenSSH Server

Though it is not needed or installing OCCAM, installing
OpenSSH Server makes it easier to work in the VirtualBox:

```
$ sudo apt install openssh-server
```

You may need to configure networking in the VirtualBox and on your host machine to be able to SSH in.

### Install Apache2

Depending on how you configured your machine, you may already have Apache2 installed: check this with

```
$ apache2 -v
```

If it is missing, install it now

```
$ apt install apache2
```

### Install Python 2.7

You currently need Python 2.7 installed to run OCCAM.

```
$ apt install python2.7
```

Note that you are dependent on system Python 2 packages, as `pip` no longer supports Python 2.

You may need to make Python 2 be `python`.

```
$ sudo sh -c 'cd /usr/bin && ln -s python2 python'
```

### Install Build Dependencies

A number of packages must be installed to build OCCAM.

```
$ sudo apt install gcc build-essential libgmp3-dev python-dev libxml2 \
  libxml2-dev zlib1g-dev python-igraph libboost-math-dev
```

## Build OCCAM

Now that you have a machine with the right dependencies set up, you can build OCCAM.  First you need to get the OCCAM repository onto your machine.  You can do this by downloading the ZIP unzipping the folder wherever you like, or by using git.

```
$ git clone https://github.com/occam-ra/occam.git
$ cd occam
$ make
```

**Note**: Contributors may want to fork the OCCAM repo and clone that.

### Install OCCAM

Pick an installation folder. We recommend `/var/www/occam` and will be using it for these instructions.  Make sure that permissions are set up correctly there so that the install can work: see below for more information on this if needed. Then install.

```
$ make INSTALL_ROOT=/var/www/occam install
```

At this point OCCAM should be ready to go.  Now you need to make sure Apache is serving it correctly.

## Set Up Apache

Apache should already be running: you just need to point the default site to your `occam/install/web` directory, set up the `ServerName` and `VirtualDirectory` and make sure that CGI is enabled.

```
$ sudo vi /etc/apache2/sites-enabled/000-default.conf
```

You'll want to add or change the following lines in that configuration file.
Note that you should set `ServerName` to whatever domain name you want the
server to run as.

```
    # Move this directive to the top of the file.
    ServerName localhost

	DocumentRoot /var/www/occam/web

	<Directory /var/www/occam/web>
		Options +ExecCGI
		AddHandler cgi-script .cgi .pl
		options Indexes FollowSymLinks
		AllowOverride All
		Require all granted
	</Directory>
```

Now enable CGI and restart the server.

```
$ a2enmod cgi
$ service apache2 restart
```

### Setting Permissions

If you are running OCCAM as a user other than `www-data`, you will need to edit `/etc/apache2/envars`. If you want to run as user `occam`, set this as follows:

```
export APACHE_RUN_USER=occam
export APACHE_RUN_GROUP=occam
```

An alternate approach is to set ownership and and permissions on the OCCAM installation so that Apache will have access. Using group `www-data` for the OCCAM installation may avoid problems on systems with existing applications that depend on the current Apache configuration.

```
$ chgrp -R www-data /var/www/occam/web
$ chmod -R 750 /var/www/occam/web
$ chmod g+s /var/www/occam/web/
$ chmod g+w /var/www/occam/web/data/
```

This will recursively change group ownership to the `www-data` group; change file permissions to [0750 = User: rwx Group: r-x World: no access)]; set new files created in this directory to have their group set to the directory's group; and add group write privileges for the `data/` subdirectory. This method avoids the insecure `chmod 777` and uses group permissions so you don't have to change your Apache user.

The last step is very important, because OCCAM creates temporary versions of the data files: the `www-data` group needs write permissions for that directory. If you don't do this last step, OCCAM will run part of the way: the front form will come up, and you can choose a data file and set search options, but when you run the search you will get a permissions error because the data file cannot be created on the server.

### Remapping the URL with aliasing

You might want to use aliasing to remap your URL and filesystem location. By default your OCCAM URL will be something like <http://localhost/occam/web>: you might want <http://localhost/occam>. You might also have other reasons for this depending on your webserver configuration.

Add this directive to your apache config file for this site:

```
Alias "/occam" "/var/www/occam/web"
```

## Trying It Out

You should be able to restart Apache and take your IP address...

```
$ sudo service apache2 restart
$ ifconfig | grep "inet addr" | head -n 1
		inet addr:10.0.0.165  Bcast:10.0.0.255  Mask:255.255.255.0
```

Now you can open a browser window (to <http://localhost/occam/web> or possibly to <http://localhost/occam> depending on aliasing) and view your fully operational OCCAM session!
