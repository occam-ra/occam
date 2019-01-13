# OCCAM: Reconstructability Analysis Tools
Copyright (c) 1990 The Portland State University OCCAM Project Team

OCCAM is a collection of software tools comprising a library
with both command-line and web interfaces for
*Reconstructability Analysis* (RA), a kind of statistical
analysis closely related to Factor Analysis and Bayesian
Belief Networks.

The OCCAM project has been developed over several decades at
Portland State University under the auspices of its creator
Prof. Martin Zwick. Programmers contributing to the work
have included Ken Willett, Joe Fusion and H. Forrest
Alexander.

This software is currently being released for the first time
as Free Software under the GPL v3 or later. Please see the
file `LICENSE` in this distribution for license terms.

As of right now, the software will be a bit challenging to
get started with. There is documentation included, but it is
rather out-of-date. The core functionality is encapsulated
in a fairly standard C++ library whose interface should be
relatively understandable to anyone familiar with both C++
and RA. Help making this software more generally and broadly
usable would be greatly appreciated.


## Installation

### VirtualBox

To create an instance of OCCAM without a dedicated Linux machine you can [Download VirtualBox](https://www.virtualbox.org/wiki/Downloads).  Select New and make sure it is of the Linux type with enough memory and storage space to run the chosen OS.

You'll want to make sure your box is "Attached to" a Bridged Adapter in Network settings for Adapter 1, but the rest of the settings based mostly on the preference of the user and limitations of the host machine.

You can then create a Linux server box by installing from an ISO, like these [Ubuntu ISOs](http://releases.ubuntu.com/16.04/).


### Install Ubuntu Server 16.04

Choose the Ubuntu Server for either 32-bit or 64-bit (depending on the host OS) from [ISOs](http://releases.ubuntu.com/16.04/).

Use at least 2GB of memory and 5GB of storage.

OR

Install Ubuntu Server 16.04 on your own hardware or other virtual machine.

OR

Skip this step and attempt to install this on an existing Ubuntu install.

During the installation you should get some options to install additional packages, you will want to install 'LAMP server'.

I also installed PostgresSQL database for possible development with that, and also OpenSSH Server so that I could SSH into the server and SCP files between any of my computers, but these are not required to get OCCAM running.

### Install Dependencies

If you didn't do it during installation you'll need to install Apache 2 and Pyhon 2.

Check to see if you have them installed and see which versions:

```
$ apache2 -v
$ python -V
```
*Note*: Must be Python 2.7

Once you verify that Apache and Python are installed, you'l need to install a number of other depencies for OCCAM:

```
$ sudo apt-get update
$ sudo apt-get install gcc build-essential libgmp3-dev python-dev libxml2 libmxl2-dev zlibg-dev python-pip
$ pip install python-igraph
```

### OCCAM Install

Now that you have a machine with the right dependencies setup, you can install and setup OCCAM.  First you need to get the OCCAM repository onto your machine.  You can do this by downloading the ZIP unzipping the folder wherever you like, or by using git.

```
$ sudo apt install git
$ git clone https://github.com/occam-ra/occam.git
$ cd occam
$ make install
```
*Note*: Contributors will likely want to clone their own forks. 

OCCAM should now be installed in the `install` folder.  You will need to create the `install/web/data` directory and give it proper permissions.

```
$ cd install/web
$ mkdir data
$ chmod 777 data
```
*Note*: These are likely not "proper" permissions, someone with better Linux experience probably knows a way to get it working without full public permisions.
*Note2*: These steps can probably be added to the Makefile.

At this point OCCAM should be all setup.  Now you need to make sure Apache is serving it correcly.

### Apache Setup

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

Finally, there are some permission issues that happen sometimes, so my solution was to edit the `/etc/apache2/envars` file to make Apache run as my default unix user (occam).  There may be another way to do this, all suggestions welcome!

In any case, you should be able to restart apache and take your IP address...

```
$ sudo service apache2 restart
$ ifconfig | grep "inet addr" | head -n 1
		inet addr:10.0.0.165  Bcast:10.0.0.255  Mask:255.255.255.0
```

Now you can open a browser window to first IP address and view your fully operational OCCAM session!

