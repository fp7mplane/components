# Anycast Probe

## 1. Installation
----------------------------------------
Set the following parameter with the path of the anycast data in the file components/anycast.py (in the components GitHub): 

```
anycast_data= [path with anycast data]
```

Copy files from the Anycast mPlane interface (from the components GitHub) into protocol-ri/:
    - `registry.json` The registry.json file, copy it into protocol-ri/mplane/.
    - `anycast.py` The Python interface, copy it into protocol-ri/mplane/components/.
    - `anycast.conf` The Anycast config file, copy it into protocol-ri/mplane/components/.
    - `supervisor.conf`  and `client.conf` The configuration file, copy them into protocol-ri/conf/.

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

In another terminal start the anycast probe as a component:

```
cd ~/protocol-ri 
python3 -m scripts/mpcom --config ./conf/anycast.conf
```

alternatively:

```
cd ~/protocol-ri
sudo python3 -m mplane.component --config ./conf/anycast.conf
```
The expected output should be:
```
Added <Service for <capability: measure (anycast-detection-ip4) when now token 7ffe4cd3 schema 2e02eb6d p/m/r 2/0/1>>
Added <Service for <capability: measure (anycast-enumeration-ip4) when now token b630c242 schema fe01ca35 p/m/r 2/0/2>>
Added <Service for <capability: measure (anycast-geolocation-ip4) when now token a65e656a schema c9c9440f p/m/r 2/0/2>>

Capability registration outcome:
anycast-detection-ip4: Ok
callback: Ok
anycast-geolocation-ip4: Ok
anycast-enumeration-ip4: Ok

```

Output from the supervisor:
```
Added <Service for <capability: measure (anycast-enumeration-ip4) when now token b630c242 schema fe01ca35 p/m/r 2/0/2>>
Added <Service for <capability: measure (anycast-geolocation-ip4) when now token a65e656a schema c9c9440f p/m/r 2/0/2>>
Added <Service for <capability: measure (anycast-detection-ip4) when now token 7ffe4cd3 schema 2e02eb6d p/m/r 2/0/1>>
Added <Service for <capability: measure (callback) when now ... future token c855a414 schema a7b45ce6 p/m/r 0/0/0>>
```

## 3. Launching an experiment
----------------------------------------
Start a client to test the component:

```
python3 -m scripts/mpcli --config mplane/components/anycast/client.conf 
```
alternatively:

```
python3 -m mplane.clientshell --config mplane/components/anycast/client.conf 
```

The expected output should be:
```
ok
mPlane client shell (rev 20.1.2015, sdk branch)
Type help or ? to list commands. ^D to exit.

|mplane|
```

Now check that the anycast capabilities is registered:
```
|mplane| listcap
Capability anycast-detection-ip4 (token 7ffe4cd3039cc8cf1ec7fa2e61697844)
Capability anycast-enumeration-ip4 (token b630c2426af0bbb831266617856ce5b9)
Capability anycast-geolocation-ip4 (token a65e656a563d20a5447605d45efe8ed6)
```

To check if an IPv4 is anycast:
```
|mplane| when now
set destination.ip4 192.36.148.17
|mplane| runcap anycast-detection-ip4
|mplane| showmeas anycast-detection-ip4-0
result: measure
    label       : anycast-detection-ip4-0
    token       : 523e8c73d0dfcaad0f67727305b33437
    when        : 2015-07-02 10:24:26.598705
    registry    : http://ict-mplane.eu/registry/core
    parameters  ( 2): 
                              source.ip4: 1.2.3.4
                         destination.ip4: 192.36.148.17
    resultvalues( 1):
          result 0:
                                     anycast: True
```
To know the number of the anycast instances for an IPv4:
    
```
|mplane| when now
set destination.ip4 192.36.148.17
|mplane| runcap anycast-enumeration-ip4
|mplane| showmeas anycast-enumeration-ip4-1
result: measure
    label       : anycast-enumeration-ip4-1
    token       : d61be207c705b521b11cdebccd3e661f
    when        : 2015-07-02 10:25:56.780926
    registry    : http://ict-mplane.eu/registry/core
    parameters  ( 2): 
                              source.ip4: 1.2.3.4
                         destination.ip4: 192.36.148.17
    resultvalues( 1):
          result 0:
                   anycast: True
                   anycast_enumeration: 12
```
To know the location of the anycast instances for an IPv4:

```
|mplane| when now
set destination.ip4 192.36.148.17
|mplane| runcap anycast-geolocation-ip4
|mplane| showmeas anycast-geolocation-ip4-2
result: measure
    label       : anycast-geolocation-ip4-2
    token       : ff482afcee375c4a8014f4faf270fe3c
    when        : 2015-07-02 10:27:20.694852
    registry    : http://ict-mplane.eu/registry/core
    parameters  ( 2): 
                              source.ip4: 1.2.3.4
                         destination.ip4: 192.36.148.17
    resultvalues( 1):
          result 0:
                                     anycast: True
                         anycast_geolocation: [{"country": "NZ", "latitude_city": "-41.3272018433", "city": "Wellington", "longitude_city": "174.804992676"}, {"country": "NZ", "latitude_city": "-41.3272018433", "city": "Wellington", "longitude_city": "174.804992676"}, {"country": "NZ", "latitude_city": "-41.3272018433", "city": "Wellington", "longitude_city": "174.804992676"}, {"country": "NZ", "latitude_city": "-41.3272018433", "city": "Wellington", "longitude_city": "174.804992676"}]
```


The anycast probe exposes the data obtained in the [anycast project](http://www.infres.enst.fr/~drossi/anycast).
