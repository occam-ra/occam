## Virtual Environments

Some users might wish to install OCCAM directly on a Linux hardware machine, bypassing machine virtualization. This is not currently easily doable, because Python 2 is needed and is no longer readily available. These instructions are retained for those who manage to get Python 2 installed. The instructions will be modified in the future when Occam is moved to Python 3.

If you install directly, we recommend using a Python virtual environment environment for OCCAM. This is particularly advisable if you are installing on a machine which contains an existing python configuration and applications which depend on it. We will give instructions for `virtualenv`.

First, install `virtualenv`:

```
$ sudo apt-get install virtualenv
$ virtualenv -p /usr/bin/python2.7 occam/
```

(or replace 'occam' with your desired directory name). We need to use `-p` instead of just running 'virtualenv occam/', which would set up the environment with Python 3.

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
