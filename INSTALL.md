# Installation

## Overview

The current version of OCCAM runs as a linux webserver. The installation procedure is fairly well defined for linux, so you should be able to get OCCAM up and running on most linux systems, but this procedure will describe the process using Ubuntu on VirtualBox.

1. Install a virtual machine or virtual environment
2. Install Ubuntu 18.04
3. Install OCCAM using the install script

### Install VirtualBox

[Download VirtualBox](https://www.virtualbox.org/wiki/Downloads), install and run it.

Select New and choose Type: Linux and Version: Ubuntu (64-bit).

You can use the default hardware settings, but adding more RAM and Hardware storage will help analyze larger datasets.

After the box is created, go into the Settings for the Box and set "Attached to" as Bridged Adapter in Network for Adapter 1.

Next you'll need to set the Virtual Optical Storage to the Ubuntu 18.04 ISO you'll download next.

### Install Ubuntu Server 18.04

Choose the Ubuntu Server for 64-bit from [ISOs](http://releases.ubuntu.com/18.04/).  Install this ISO into the Virtual Optical Disk in the Storate Settings for your Box.

Start the Box and then follow the prompts for installing Ubuntu Server.  You should be able to use all the default settings, but you may want to check the box to install OpenSSH Server so that you can connect using SSH to continue the rest of the install.

When prompted to set the name, server name, and username, it's recommended here to use `occam` for them all.  Password is left to your discretion.  Reboot when the installation is complete.

### Install OCCAM

Once the server reboots you can log in as `occam`.  Then run the following commands:

```
$ git clone https://github.com/occam-ra/occam.git
$ cd occam
$ ./install_occam.sh
```

OCCAM everything is finished installing you should now have OCCAM installed in the `install` folder.

Get the IP address by running the following command:

```
$ ifconfig | grep "inet" | head -n 1
```

Now you should be able to browse to that IP address in your web browser of choice and see a running OCCAM installation.
