#! /bin/bash

date >crashtest.log
python basic.py examples/bw21t08.in >>crashtest.log 2>&1
date >>crashtest.log

