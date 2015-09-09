TrafficCop
====

[TrafficCop](https://engineering.opendns.com/2015/08/31/generating-iptables-rules-with-trafficcop/) is an iptables rule generator. It helps you:

1. Enable iptables logging via [ulogd](http://www.netfilter.org/projects/ulogd/)
2. Parse those logs to generate both a "traffic report" and a list of iptables rules

You can use the generated iptables rules as a starting point, to set an initial baseline of traffic control for your server.

Prerequisites
-------------
* Python 2.7
  * Click
  * PrettyTable
* iptables, enabled
* ulog2 (apt-get/yum install ulogd2)

Installing ulogd:
```bash
sudo apt-get (or yum) install ulogd2
```

Installing required Python modules:
```bash
pip install -r requirements.txt
```

Vagrant Quick-Demo
------------------
```bash
$ cd TrafficCop
$ vagrant up
$ vagrant ssh
$ cd /vagrant
$ ./tcop enable
(choose yes at the prompts)

# let's generate some traffic
$ curl www.google.com
$ exit
$ vagrant ssh
$ cd /vagrant
$ ./tcop report

# you should see the outbound to google and the inbound ssh, at least
# enjoy!
```

Getting Started
---------------
Check out your current iptables ruleset:
```bash
sudo /sbin/iptables -L
```
Notice the ACCEPT and DROP statements

Now let's enable logging:
```bash
./tcop enable
```
This will backup your current config so we can always return to it.
It will also prompt you a few times to make sure you know what you're doing.

If all went well, logging is on!
If you kept the ulog config default, you should see logs here:
```bash
tail -f /var/log/ulog/syslogemu.log
```

To run a traffic report and generate iptables rules:
```bash
./tcop report
```

You can run the report at any time, but it's best to let it run for a few days/weeks to get a more complete understanding of all the external dependencies and users of the host.

To set your rules back to the way they were before mucking with them:
```bash
sudo /sbin/iptables-restore [path to backup rules]
```
