# Installation

# Overview

The current version of OCCAM runs on a linux webserver. The installation procedure is fairly well defined for linux, so you should be able to get OCCAM up and running on your linux system. This will probably require the use of virtual environment (described below) or some other method to control the python environment. For most users, the recommended installation method at this time is to use VirtualBox, which will let you create a fully containerized linux machine inside your existing OS. This will isolate OCCAM inside the VirtualBox and not require configuration changes to your larger system. The procedure is as follows:

1. Install a virtual machine or virtual environment, and install Ubuntu or some other Linux server on your (virtual) machine, and install dependencies
2. Install OCCAM using git
3. Install apache and configure it for CGI-bin
4. Set file ownership and permissions to allow apache to access the files

So let's begin:

## Install VirtualBox

To create an instance of OCCAM without a dedicated Linux machine you can [Download VirtualBox](https://www.virtualbox.org/wiki/Downloads).  Select New and make sure it is of the Linux type with enough memory and storage space to run the chosen OS.

You'll want to make sure your box is "Attached to" a Bridged Adapter in Network settings for Adapter 1, but the rest of the settings based mostly on the preference of the user and limitations of the host machine.

You can then create a Linux server box by installing from an ISO, like these [Ubuntu ISOs](http://releases.ubuntu.com/16.04/).

## Install Ubuntu Server 16.04

Choose the Ubuntu Server for either 32-bit or 64-bit (depending on the host OS) from [ISOs](http://releases.ubuntu.com/16.04/).

Use at least 2GB of memory and 5GB of storage.

**OR**

Install Ubuntu Server 16.04 on your own hardware or other virtual machine.

**OR**

Skip this step and attempt to install this on an existing Ubuntu install.

During the installation you should get some options to install additional packages, you will want to install 'LAMP server'.

I also installed PostgresSQL database for possible development with that, and also OpenSSH Server so that I could SSH into the server and SCP files between any of my computers, but these are not required to get OCCAM running.

## Install Dependencies

If you didn't do it during installation you'll need to install Apache2 and Python2.

Check to see if you have them installed and see which versions:

```
$ apache2 -v
$ python -V
```
**Note**: Must be Python 2.7.x

Once you verify that Apache and Python are installed, you'l need to install a number of other depencies for OCCAM:

```
$ sudo apt-get update
$ sudo apt-get install gcc build-essential libgmp3-dev python-dev libxml2 libxml2-dev zlib1g-dev python-pip
$ pip install python-igraph
```

## Virtual Environments

Some users might wish to install OCCAM directly on a linux hardware machine, bypassing machine virtualization. Doing so will probably require virtual environments or some other method to let you control your python environment for OCCAM (particularly if you are installing on a machine which contains an existing python configuration and applications which depend on it. Here is how to do that. First, install virtualenv:

```
$ sudo apt-get install virtualenv

$ virtualenv -p /usr/bin/python2.7 occam/
```
(or replace 'occam' with your desired directory name). We need to use -p instead of just running 'virtualenv occam/', which would set up the environment, but not with python2.7, which is what we need.

Now activate the environment:
```
$ source occam/bin/activate
```

When the environment is active, its name will appear in front of your command prompt, like:

```
(occam) user@host $
```
 
Once the environment is activated, anything that you do that makes environment changes (like install packages) will now change your virtual environment configuration, and not your global configuration. With an active virtual environment, using pip to install, uninstall, or upgrade packages (or do anything else that makes changes to your python environment) will now make those package changes to the virtual environment and not your global environment, so you could have one version of a package for the occam environment and another for your global configuration, and yet another in a different virtual environment for a different application. This will avoid version conflicts and allow your existing python applications to run as they currently do, and to run OCCAM with the interpreter and package version that it needs.

Now that you have done the setup of your virtual machine or environment, you can actually install OCCAM.

## Install OCCAM

Now that you have a machine with the right dependencies set up, you can install and setup OCCAM.  First you need to get the OCCAM repository onto your machine.  You can do this by downloading the ZIP unzipping the folder wherever you like, or by using git.

```
$ sudo apt install git
$ git clone https://github.com/occam-ra/occam.git
$ cd occam
$ sudo make install
```
**Note**: It is *very* important, on many systems, to do 'sudo make install' instead of just 'make install'. If make fails will a permissions error and the install directory is not created properly, your install will not work even if you follow all the rest of the steps correctly. Make sure that make completes properly, and if it fails with a permissions error, rerun it with 'sudo'
**Note**: Contributors will likely want to clone their own forks. 

OCCAM should now be installed in the `install` folder.

At this point OCCAM should be all setup.  Now you need to make sure Apache is serving it correcly.

## Setup Apache

Apache should already be running, so you just need to point the default site to your `occam/install/web` directory, setup the VirtualDirectory and make sure that CGI is enabled.

```
$ sudo a2enmod cgi
$ sudo vi /etc/apache2/sites-enabled/000-default.conf
```

You'll want to add or change the following lines in that configuration file:

```
	#DocumentRoot /path/to/occam/install/web
	# e.g.
	DocumentRoot /home/occam/occam/install/web

	# Add this toward the bottom
	#<Directory /path/to/occam/install/web>
	# e.g.
	<Directory /home/occam/occam/install/web>
		Options +ExecCGI
		AddHandler cgi-script .cgi .pl
		options Indexes FollowSymLinks
		AllowOverride All
		Require all granted
	</Directory>
```

Finally, there are some permission issues that happen sometimes, so my solution was to edit the `/etc/apache2/envars` file to make Apache run as my default unix user (occam):

```
$ sudo vi /etc/apache2/envvars
```

Edit to use your default unix user/group in place of `occam`.

```
# CHANGE
# export APACHE_RUN_USER=www-data
# export APACHE_RUN_GROUP=www-data
# TO
export APACHE_RUN_USER=occam
export APACHE_RUN_GROUP=occam
```

Another approach to this is to set owernship and permissions so that apache will have access without having to change the apache user (which, again, might cause problems on systems with existing applications that depend on the current apache configuration). 

From your OCCAM install directory (the install/ directory created when you ran make), do:

```
$ chown -R snoopy web/

$ chgrp -R www-data web/

$ chmod -R 750 web/

$ chmod g+s web/
```
This will recursively set ownership of the occam web directory to the user you desire on your system; change group ownership to the www-data group; change file permissions to [0750 = User: rwx  Group: r-x  World: --- (i.e. World: no access)]; set new files created in this directory to have their group set to the directory's group.

If you stop at this point, OCCAM will appear to work at first glance. The front page will serve with the initial form, you can choose 'search' and then enter a file and search options, but when you run the search it will not completely properly, and you will get a permissions error. 

The last step is to do:
```
$ chmod g+w web/data/
```
which will add group write privileges for the data/ subdirectory, which is necessary because OCCAM creates temporary versions of the data files, so the www-data group needs write permissions for that directory. If you don't do this last step, OCCAM will run part of the way - the front form will come up, and you can choose a data file and set search options, but when you run the search you will get a permissions error because the data file cannot be created on the server.

Now, you should be able to restart apache and take your IP address...

```
$ sudo service apache2 restart
$ ifconfig | grep "inet addr" | head -n 1
		inet addr:10.0.0.165  Bcast:10.0.0.255  Mask:255.255.255.0
```

Now you can open a browser window (probably to http://localhost/occam/install/web to first IP address and view your fully operational OCCAM session!
