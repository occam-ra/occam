# Installation

## Install Virtual Environment

Per Guy - [The Hitchhikers Guide to Pipenv & Virtual Environments](https://docs.python-guide.org/dev/virtualenvs/), which is recommended for those who would like to install on an existing Linux machine without needing to change their existing Python setup.

If you are on a Windows machine, you will probably want to use VirtualBox.

### Install VirtualBox

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

## Install OCCAM

Now that you have a machine with the right dependencies setup, you can install and setup OCCAM.  First you need to get the OCCAM repository onto your machine.  You can do this by downloading the ZIP unzipping the folder wherever you like, or by using git.

```
$ sudo apt install git
$ git clone https://github.com/occam-ra/occam.git
$ cd occam
$ make install
```
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

There may be another way to do this, all suggestions welcome!

In any case, you should be able to restart apache and take your IP address...

```
$ sudo service apache2 restart
$ ifconfig | grep "inet addr" | head -n 1
		inet addr:10.0.0.165  Bcast:10.0.0.255  Mask:255.255.255.0
```

Now you can open a browser window to first IP address and view your fully operational OCCAM session!
