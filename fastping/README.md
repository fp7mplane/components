# Fastping Probe

## 1. Installation
----------------------------------------

Install fastPing required python2
The code for the bash version is in fastping/fastpingBash (in the components GitHub), for more information about the bash version refer to the D2.2 or to the [software description](http://www.ict-mplane.eu/public/fastping).

Copy files from the Fastping mPlane interface (from the components GitHub) into protocol-ri/:

- `registry.json` The registry.json file, copy it into protocol-ri/mplane/.
- `fastping.py` The Python interface, copy it into protocol-ri/mplane/components/.
- `fastping.conf` The fastPing config file, copy it into protocol-ri/mplane/components/.
- `supervisor.conf` and `client.conf`, The configuration file, copy them into protocol-ri/conf/.


## 2. Launching the probe
----------------------------------------

In a terminal window start supervisor:
```
cd ~/protocol-ri
python3 -m scripts/mpsup --config ./conf/supervisor.conf
```
alternatively:
```
cd ~/protocol-ri
python3 -m mplane.supervisor --config ./conf/supervisor.conf
```


In another terminal start the fastPing probe as a component:
```
cd ~/protocol-ri
sudo python3 -m scripts/mpcom --config ./conf/fastping.conf
```
alternatively:
```
cd ~/protocol-ri
sudo python3 -m mplane.component --config ./conf/fastping.conf
```

The expected output should be:
```
Added <Service for <capability: measure (fastping-ip4) when now ... future / 1s token e7735f25 schema 2f2af5dc p/m/r 11/0/1>>

Capability registration outcome:
callback: Ok
fastping-ip4: Ok

Checking for Specifications...
```

Output from the supervisor:
```
Added <Service for <capability: measure (fastping-ip4) when now ... future / 1s token e7735f25 schema 2f2af5dc p/m/r 11/0/1>>
Added <Service for <capability: measure (callback) when now ... future token c855a414 schema a7b45ce6 p/m/r 0/0/0>>
```

## 3. Launching an experiment
----------------------------------------
Start a client to test the component:

```
python3 -m scripts/mpcli --config mplane/components/fastping/client.conf
```
alternatively:
```
python3 -m mplane.clientshell --config mplane/components/fastping/client.conf
```

The expected output should be:
```
ok
mPlane client shell (rev 20.1.2015, sdk branch)
Type help or ? to list commands. ^D to exit.

|mplane|
```

Now check that the fastping capability is registered:
```
|mplane| listcap
Capability fastping-ip4 (token e7735f25459c4e7efc0a1fcba7e9e5ee)
```

Fastping as the name implies is aimed at large-scale measurement. It follows that a large quantity of data is generated in a short time, making indirect export the preferred way to report measurement data. In case the results are needed in band (i.e., within the same TCP connection), then the simpler mplane-ping probe is a better candidate.

For the sake of the example, the following command launches a specification for an experiment lasting 10 seconds, using 8.8.8.8 as destination and probing it 10 times during the measurement, finally uploading results to a FTP server via:
```
|mplane| when now + 1s / 10s
         set destinations.ip4 8.8.8.8
         set cycleduration.s 10
         set period.s 1
         set numberCycle 1
         set ftp.password ''
         set ftp.port 21
         set ftp.ip4 127.0.0.1
         set ftp.currdir up
         set ftp.user anonymous
         set ftp.password ''
         set ftp.ispsv True

|mplane| runcap fastping-ip4
source.ip4 = 1.2.3.4
ok
```

When the experiment is over, for see the result:

```
|mplane| showmeas fastping-ip4-0
result: measure
    label       : fastping-ip4-0
    token       : 3951f51b68bedf7e91ac4fb7bc7485e6
    when        : 2015-07-01 17:52:36.507573 ... 2015-07-01 17:52:58.694320
    registry    : http://ict-mplane.eu/registry/core
    parameters  (11):
                             numberCycle: 1
                             ftp.currdir: up
                            ftp.password: ''
                         cycleduration.s: 10
                                ftp.port: 21
                        destinations.ip4: 8.8.8.8
                              source.ip4: 1.2.3.4
                                period.s: 1
                                 ftp.ip4: 127.0.0.1
                               ftp.ispsv: True
                                ftp.user: anonymous
    resultvalues( 1):
          result 0:
          file.list: danilo_1435773157.rw,danilo_1435773157-1.st,danilo_1435773157-1.sm,danilo_1435773157-1.qd
```


The fastping probes supports the setup of more complex experiments via a plural  "destinations" keyword supporting a flexible syntax examplified as follows:

- specify multiple hosts

```
set destinations.ip4 8.8.8.8 8.8.8.4
```
- specify IPv4 ranges:
```
set destinations.ip4 8.8.0.0/24
```
- specify list of IPv4 ranges:

```
set destinations.ip4 8.8.0.0/24 137.194.0.0/24
```
- mixing everything above

```
set destinations.ip4 8.8.0.0/24 8.8.8.8 137.194.0.0/24
```

Fastping has been used in the anycast measurement campaign, for more information and results at a glance [anycast project](http://www.infres.enst.fr/~drossi/anycast) 
