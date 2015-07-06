#Tstat probe

The Tstat probe setup consists of 3 main parts:

- [Tstat](<http://tstat.polito.it>) is a passive sniffer able to provide several insight on the traffic patterns at both the the network and transport levels.
- mPlane protocol Reference Implementation - Available [here](<https://github.com/fp7mplane/protocol-ri>), Component-based framework written in Python to enable cooperation of mPlane compliant devices.
- Tstat probe - mPlane SDK interface, available [here](<https://github.com/fp7mplane/components/tree/master/tstat>). Python interface connecting the Tstat probe to the mPlane.

##Installing Tstat
Download the source code from [tstat](http://tstat.polito.it/download/tstat-latest.tar.gz).
Optional prerequisites for the C module:
- zlib
- rrdtool

Tstat should compile and run under Unix-based systems.

```
$ ./autogen.sh
$ ./configure
$ make
$ make install
```

## Run Tstat

Tstat requires at least sudoer priviledges to run. Here is an example of how to launch it:

```
$ sudo tstat -l -i eth0 -s tstat_output_logs -T tstat-conf/runtime.conf -R tstat-conf/rrd.conf -r ./rrdfiles/
```

**-l**: enable live capture using libpcap

**-i** interface: specifies the interface to be used to capture traffic

**-s** dir: puts the trace analysis results into directory tree dir (otherwise will be <file>.out)

**-T** runtime.conf: configuration file to enable/disable dumping of traces and logs at runtime

**-R** conf: specify the configuration file for integration with RRDtool.

**-r** path: path to use to create/update the RRDtool database

For more information, please refer to the official [Tstat website](http://tstat.polito.it)


##Installing the mPlane framework and the Tstat proxy

Checkout the protocol reference implementation.

```
$ git clone https://github.com/fp7mplane/protocol-ri.git
```

Move to the components folder, rename it and replace it with the github one.

```
$ cd mplane/components
$ mv components components.orig (or rm -rf components)
$ git clone https://github.com/fp7mplane/components/
$ cd ../../
```

Add to the `conf/supervisor.conf` the missing 
capabilities below [Authorizations]: 

```
tstat-log_http_complete = guest,admin
tstat-exporter_streaming = guest,admin
tstat-log_rrds = guest,admin
tstat-exporter_rrd = guest,admin
tstat-exporter_log = guest,admin
repository-collect_rrd = guest,admin
repository-collect_streaming = guest,admin
repository-collect_log = guest,admin
```

##Running the supervisor
In the open shell, run:

```
$ export PYTHONPATH=.
$ ./scripts/mpsup --config ./conf/supervisor.conf
```

##Running the tstat proxy
Change the paths to Tstat's configuration files in `./mplane/components/tstat/conf/tstat.conf`:

```
runtimeconf = /tmp/runtime.conf
tstat_rrd_path = /tmp/rrdfiles/
```

Open a new terminal, move to the protocol-ri folder and run:

```
$ export PYTHONPATH=.
$ ./scripts/mpcom --config ./mplane/components/tstat/conf/tstat.conf
Added <Service for <capability: measure (tstat-log_tcp_complete-core) when now ... future token 7ee0a281 schema 39952155 p/m/r 0/3/42>>
Added <Service for <capability: measure (tstat-log_tcp_complete-end_to_end) when now ... future token 1ab5668d schema ce6233ed p/m/r 0/3/7>>
Added <Service for <capability: measure (tstat-log_tcp_complete-tcp_options) when now ... future token 68cc4936 schema 62657c35 p/m/r 0/3/46>>
Added <Service for <capability: measure (tstat-log_tcp_complete-p2p_stats) when now ... future token 9963ddd3 schema 348428a8 p/m/r 0/3/6>>
Added <Service for <capability: measure (tstat-log_tcp_complete-layer7) when now ... future token c03c028d schema c445bac9 p/m/r 0/3/4>>
Added <Service for <capability: measure (tstat-log_rrds) when now ... future token f0bab5b4 schema 3231d66d p/m/r 0/3/9>>
Added <Service for <capability: measure (tstat-exporter_rrd) when past ... future token 58d1109f schema 1216bc3b p/m/r 1/3/3>>
Added <Service for <capability: measure (tstat-log_http_complete) when now ... future token d8c8fa10 schema d2deb3c1 p/m/r 0/3/17>>
Added <Service for <capability: measure (tstat-exporter_streaming) when now ... future token 2ad7da68 schema ffb9654b p/m/r 4/3/0>>
Added <Service for <capability: measure (tstat-exporter_log) when past ... future token eb1e0c4f schema 9baaae2e p/m/r 1/3/0>>
```


##Running the repository proxy
Open a new terminal, move to the protocol-ri folder and run:

```
$ export PYTHONPATH=.
$ ./scripts/mpcom --config ./mplane/components/tstat/conf/tstatrepository.conf
Added <Service for <capability: measure (repository-collect_rrd) when past ... future token 5628ceb3 schema 1216bc3b p/m/r 1/3/3>>
Added <Service for <capability: measure (repository-collect_streaming) when now ... future token 39de2de6 schema 9baaae2e p/m/r 1/3/0>>
Added <Service for <capability: measure (repository-collect_log) when past ... future token 0ccb3dc4 schema 9baaae2e p/m/r 1/3/0>>
```

##Running the client
Open a new terminal, move to the protocol-ri folder and run:

``` 
$ export PYTHONPATH=.
$ ./scripts/mpcli --config ./conf/client.conf
ok
mPlane client shell (rev 20.1.2015, sdk branch)
Type help or ? to list commands. ^D to exit.
|mplane| listcap
Capability repository-collect_log (token 0ccb3dc4c3290bbbb63caeb1a9f44a6d)
Capability repository-collect_rrd (token 5628ceb366cf23076ab131f701b6dbd0)
Capability repository-collect_streaming (token 39de2de6bf9e6b1423cb42f258a40683)
Capability tstat-exporter_log (token eb1e0c4f3b91673a52733948ef0a9c98)
Capability tstat-exporter_rrd (token 58d1109f591c69dba93193bc88688131)
Capability tstat-exporter_streaming (token 2ad7da68b76a91e9ed96c8d90c0df4b3)
Capability tstat-log_http_complete (token d8c8fa10aa833948024fc18477f1d69b)
Capability tstat-log_rrds (token f0bab5b4e6305b9faf5e4bdbdc4f71a5)
Capability tstat-log_tcp_complete-core (token 7ee0a2812d9decc8085f2b204df0af7d)
Capability tstat-log_tcp_complete-end_to_end (token 1ab5668dd6da4000cee08007cee23a73)
Capability tstat-log_tcp_complete-layer7 (token c03c028db352b9a41852cad68b37df4b)
Capability tstat-log_tcp_complete-p2p_stats (token 9963ddd359a679e6b48c0c9d0b282782)
Capability tstat-log_tcp_complete-tcp_options (token 68cc4936ffec4c0aab829796d8a07c74)
|mplane|
```

## Activating passive measurements
The proxy allows to activate all passive measurements offered by Tstat.
Check [here](http://tstat.tlc.polito.it/measure.shtml) for a complete documentation.

For instance, to activate the collection of Core TCP set in log_tcp_complete for 30 min, in the client run:

```
|mplane| runcap tstat-log_tcp_complete-core
|when| = now + 30m
```

To activate the RRD collection forever, run:

```
|mplane| runcap tstat-log_rrds
|when| = now + inf
```

NOTE: To reset the scheduling option `when` you might need to run:

```
|mplane| unset when
```

## Activating indirect log and rrd exporting:
Currently the proxy offers three different indirect exporting approaches

1. Log bulk exporter
2. Log streaming exporter
3. RRD exporter


### Activating log streaming exporter:

This exporter enables the streaming of logs which are collected in real-time by Tstat.
The code contained in file `tstatrepository.py` acts as a simple endpoint server which receives the streamed logs and print them to the stdout.

For instance, to activate the streaming indirect export of log_tcp_complete for 1 day, run in the client:

```
|mplane| runcap tstat-exporter_streaming
|when| = now + 1d
log.folder = /path/to/log/folder/
log.time = 60
log.type = log_tcp_complete
repo.url = 127.0.0.1:9011
ok
```

NOTE: the `repo.url` contains the IP address of the repository and the port value associated to `repository_streaming_port` in `tstatrepository.conf`.

