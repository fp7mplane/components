#Tstat probe

The Tstat probe setup consists of 3 main parts:

- [Tstat](<http://tstat.polito.it>): a passive sniffer able to provide several insight on the traffic patterns at both the network and the transport levels.
- [mPlane Protocol Reference Implementation](<https://github.com/fp7mplane/protocol-ri>): a component-based framework written in Python to enable cooperation of mPlane compliant devices.
- [Tstat mPlane proxy](<https://github.com/fp7mplane/components/tree/master/tstat>): a Python interface connecting the Tstat probe to the mPlane protocol.

##Installing Tstat
Download the source code from [Tstat](http://tstat.polito.it/download/tstat-latest.tar.gz).
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

## Running Tstat

Tstat requires at least **sudoer** privileges to run. Here is an example of how to run it:

```
$ sudo tstat -l -i eth0 -s tstat_output_logs -T tstat-conf/runtime.conf -R tstat-conf/rrd.conf -r /rrdfiles/
```

**-l**: enables live capture using libpcap

**-i** interface: specifies the interface to be used to capture traffic

**-s** dir: puts the results into directory "dir"

**-T** runtime.conf: configuration file to enable/disable logs at runtime

**-R** conf: specifies the configuration file for integration with RRDtool.

**-r** path: path where to create/update the RRDtool database

For more information, please refer to the official [Tstat website](http://tstat.polito.it)


##Installing the mPlane framework and the Tstat proxy

Checkout the protocol reference implementation.

```
$ git clone https://github.com/fp7mplane/protocol-ri.git
```

Enter the __protocol-ri/mplane__ folder and rename (or remove) __components__. Then, check out the one available on github.

```
$ cd protocol-ri/mplane/
$ mv components components.orig (or rm -rf components)
$ git clone https://github.com/fp7mplane/components/
$ cd ../
```

Add to the `[Authorizations]` section of the `conf/supervisor.conf` file the new supported capabilities listed below:

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
Open a new terminal, enter __protocol-ri__, and execute:

```
$ export PYTHONPATH=.
$ ./scripts/mpsup --config ./conf/supervisor.conf
```

##Running the Tstat proxy
Change the paths inside Tstat's configuration files in `./mplane/components/tstat/conf/tstat.conf`. If you run the Tstat as mentioned above, change the paths to:

NOTE: Install [Python-rrdtool](https://pypi.python.org/pypi/python-rrdtool/1.4.7) on the Tstat proxy machine.

```
runtimeconf = PATH_TO_TSTAT/tstat-conf/runtime.conf
tstat_rrd_path = /rrdfiles/
```

Open a new terminal, enter __protocol-ri__ folder and execute:

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
Open a new terminal, create a certificate using the `create_component_cert.sh` script for repository proxy. Please, refer to [HOWTO.txt](https://github.com/fp7mplane/protocol-ri/blob/master/PKI/HOWTO.txt) for more information.

**NOTE**: it is recommended to use `Repository-Polito` as a name for the certificate in order to be compatible with `tstatrepository.conf` by default.

Enter to the __protocol-ri__ folder and execute:

```
$ export PYTHONPATH=.
$ ./scripts/mpcom --config ./mplane/components/tstat/conf/tstatrepository.conf
Added <Service for <capability: measure (repository-collect_rrd) when past ... future token 5628ceb3 schema 1216bc3b p/m/r 1/3/3>>
Added <Service for <capability: measure (repository-collect_streaming) when now ... future token 39de2de6 schema 9baaae2e p/m/r 1/3/0>>
Added <Service for <capability: measure (repository-collect_log) when past ... future token 0ccb3dc4 schema 9baaae2e p/m/r 1/3/0>>
```

**NOTE**: The repository proxy expected that the [Graphite](http://graphite.wikidot.com/installation) and [DBStream](https://github.com/arbaer/dbstream) are running on default setting.


##Running the client
Open a new terminal, enter the __protocol-ri__ folder and execute:

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
The proxy allows the activation of all passive measurements offered by Tstat.
Check [here](http://tstat.tlc.polito.it/measure.shtml) for a complete documentation.

For instance, to activate the collection of Core TCP set in log_tcp_complete for 30 min, execute the following instructions in the client shell:

```
|mplane| runcap tstat-log_tcp_complete-core
|when| = now + 30m
```

To activate the RRD collection forever, run:

```
|mplane| runcap tstat-log_rrds
|when| = now + inf
```

**NOTE**: To reset the scheduling option `when` you need to run:

```
|mplane| unset when
```

## Activating indirect log and RRD exporting
Currently the proxy offers three different indirect exporting approaches:

1. Log bulk exporter
2. Log streaming exporter
3. RRD exporter

### Activating Log bulk exporter

The Tstat proxy sends log files collected by Tstat to the repository proxy, The log files are then stored in [DBStream](https://github.com/arbaer/dbstream).

```
|mplane| runcap tstat-exporter_log
repository.url = localhost:3000
ok
```

**NOTE**: The `repository.url` contains the IP address of the repository and the port value associated to `repository_log_port`.


### Activating log streaming exporter

This exporter enables the streaming of logs collected in real-time by Tstat.
The code contained in `tstatrepository.py` acts as a simple endpoint server which receives the streamed logs and redirect them to stdout.

For instance, to activate the streaming indirect export of log_tcp_complete for 1 day, execute the following instructions in the client shell:

```
|mplane| runcap tstat-exporter_streaming
|when| = now + 1d
log.folder = /path/to/log/folder/
log.time = 60
log.type = log_tcp_complete
repository.url = localhost:9001
ok
```

**NOTE**: The `repository.url` contains the IP address of the repository and the port value associated to `repository_streaming_port` in `tstatrepository.conf`.

### Activating RRD exporter

The Tstat proxy sends the RRD files collected by the Tstat to the repository proxy. The RRD files are then sent to the Graphite for storage and visualization.

For instance, to activate the RRD indirect export form now to 1 hour, execute in the client shell:

```
|mplane| runcap tstat-exporter_rrd
|when| = now + 1h
repository.url = localhost:9000
ok
```

The data will be visible on Graphite web interface.

**NOTE**: The `repository.url` contains the IP address of the repository and the port value associated to `repository_rrd_port`.

