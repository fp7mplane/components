#OTT probe

The fully operational OTT probe setup consists of 3 main parts:

- OTT probe. C++ measurement module, available on NETvisor site (see below). You can read about its functionality and the collected metrics at <https://www.ict-mplane.eu/public/ott-probe>.
- mPlane protocol Reference Implementation, available on GitHub. Component based framework written in Python to enable cooperation of mPlane compliant devices.
- OTT probe - mPlane SDK interface, available on GitHub. Python interface enabling OTT probe to communicate with other mPlane components.

##Installing OTT probe
Prerequisite for the C++ module:

- `libcurl.so.4`  
- `boost_program_options`  
- `libpthread`  
- `libz`  
- `libssl`  
- `libreactor` - published by NETvisor Ltd.  
- `probe-ott` published by NETvisor Ltd.

The published modules are avaible at <http://tufaweb.netvisor.hu/ottdemo/mplane-ottmodule.tar.gz>, or at http://tufaweb.netvisor.hu/mplane/ott-probe/mplane-ottmodule.tar.gz. To speed up testing there is no need to compile it from source as it is already avaible for various platforms:

- ar71xx (tested on OpenWRT 12.04)  
- x86_64 (tested on Ubuntu 14.04)  
- i386 (tested on CentOS release 6.5)  

If there is any problem (or a new platform is requested) please contact <gabor.molnar@netvisor.hu>.

Copy probe-ott to your PATH ( `/usr/bin` ) and add libreactor to `LD_LIBRARY_PATH`. The easiest way to check that all the libraries are installed is to run the object file:
```
$ probe-ott
the option '--slot' is required but missing
```
If it fails with the aforementioned error, the measurement module is configured well.

Tested protocols:

- HLS - HTTP Live streaming
  - <http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8>
  - <http://skylivehls.cdnlabs.fastweb.it/217851/tg24/index.m3u8>

- IIS - Smooth streaming
  - <http://skylivehss.cdnlabs.fastweb.it/227324/tg24.isml/Manifest>


##Installing the mPlane framework and the OTT-probe interface
In the following guide we use the following legend:

  \<ott-probe_installdir>	the directory where the OTT-probe binary (`probe-ott`) has been installed (eg. `/usr/bin`)

  \<protocol-ri_dir>	the directory where the GitHub repository of the mPlane protocol reference implementation has been cloned to  (eg. `/home/<mplane_user>/protocol-ri`)

  \<components_dir>	the directory where the GitHub repository of the components (this repository) has been cloned to  (eg. `/home/<mplane_user>/components`).

Put `<ott-probe_installdir>` into the `PATH` variable, eg. 
```
export PATH=$PATH:<ott-probe_installdir>
```
Put `<protocol-ri_dir>` into the `PYTHONPATH` variable, eg.
```
export PYTHONPATH=$PYTHONPATH:<protocol-ri_dir>
```

Copy the ott-probe interface stuff (`<components_dir>\ott-probe` folder) into  `<protocol-ri_dir>/mplane/components`. This directory should contains the followings:

- `ott-registry.json`    The registry.json file containing the needed extensions for the OTT-probe (core registry is included within). It can be also downloaded from http://tufaweb.netvisor.hu/mplane/ott-probe/ott-registry.json. This is an extended version of the coreJSON file, with all the needed definitions for **ott-probe**.
- `ott.py`    The Python interface
- `supervisor.conf`,`client.conf`, `component.conf`    The config files for running OTT in the component framework
- `ott-capabilities`	The capabilities file, does not needed for installation
- `README.md`	This file.

Adjust the parameters in the `ott.conf` file if needed (e.g. path to certificates, supervisor address, client port and address, roles, etc).

In a terminal window start supervisor:
```
root@h139-40:~/protocol-ri# test2@h139-40:~/protocol-ri$ scripts/mpsup --config mplane/components/ott-probe/supervisor.conf
ListenerHttpComponent running on port 8890

```
In another terminal start the OTT probe as a component and check if communication is established and the probe capabilities are registered with the supervisor:
```
test2@h139-40:~/protocol-ri$ scripts/mpcom --config mplane/components/ott-probe/component.conf
Added <Service for <capability: measure (ott-download) when now ... future / 10s token b77698ec schema 33a0f637 p/m/r 2/0/8>>
Added <Service for <capability: measure (ping-average-ip4) when now ... future / 1s token a74fabd1 schema e2ca42e6 p/m/r 2/0/4>>
Added <Service for <capability: measure (ping-detail-ip4) when now ... future / 1s token 75cd8c84 schema db8ef547 p/m/r 2/0/2>>

Capability registration outcome:
ping-detail-ip4: Ok
ping-average-ip4: Ok
ott-download: Ok
callback: Ok

Checking for Specifications...

```
Now we can start a clientshell in a third window to test the measurement functionalities:
```
test2@h139-40:~/protocol-ri$ scripts/mpcli --config mplane/components/ott-probe/client.conf
ok
mPlane client shell (rev 20.1.2015, sdk branch)
Type help or ? to list commands. ^D to exit.

|mplane|
```

Now check that capabilities are registered and run a measurement:
```
|mplane| listcap
Capability ott-download (token b77698ecef311f599940612f51ac7e27)
Capability ping-average-ip4 (token a74fabd15ef8bbaaf68eb106a6c1c54e)
Capability ping-detail-ip4 (token 75cd8c844dce30a09c579d9fc89caa3d)
|mplane| runcap ott-download
|when| = now + 30s / 10s
content.url = http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8
source.ip4 = 127.0.0.1
ok
|mplane| listmeas
Receipt ott-download-0 (token b5133e57c985a7194cb51caebf552bc9): now + 30s / 10s
|mplane|
```
During this we should see something similar in the component window, showing the launched application and than the receipt:
```
<Service for <capability: measure (ott-download) when now ... future / 10s token 0a01b50e schema 503f24c6 p/m/r 2/0/8>> matches <specification: measure (ott-download-0) when now + 30s / 10s token 0a4f3eac schema 503f24c6 p(v)/m/r 2(2)/0/8>
Will interrupt <Job for <specification: measure (ott-download-0) when now + 30s / 10s token 0a4f3eac schema 503f24c6 p(v)/m/r 2(2)/0/8>> after 30.0 sec
Scheduling <Job for <specification: measure (ott-download-0) when now + 30s / 10s token 0a4f3eac schema 503f24c6 p(v)/m/r 2(2)/0/8>> immediately

2015-06-10 10:58:33.906406: running probe-ott --slot -1 --mplane 10 --url http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8Returning <receipt:  (ott-download-0)0a4f3eacabd93030d32da1ede87875f4>

```
After a while we can notice the result notification in the component window as the measurement has been finished:
```
<result: measure (ott-download-0) when 2015-06-10 10:58:34.969026 token 0a4f3eac schema 503f24c6 p/m/r(r) 2/0/8(1)>
Result for ott-download-0 successfully returned!

```
We can now check the results in the client window:
```
|mplane| listmeas
Receipt ott-download-0 (token b5133e57c985a7194cb51caebf552bc9): now + 30s / 10s
|mplane| listmeas
Result  ott-download-0 (token b5133e57c985a7194cb51caebf552bc9): 2015-06-10 10:58:34.969026
|mplane| showmeas ott-download-0
result: measure
    label       : ott-download-0
    token       : b5133e57c985a7194cb51caebf552bc9
    when        : 2015-06-10 10:58:34.969026
    parameters  ( 2):
                             content.url: http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8
                              source.ip4: 127.0.0.1
    resultvalues( 1):
          result 0:
                                        time: 2015-06-10 10:58:34.969026
                      bandwidth.nominal.kbps: 720
                               http.code.max: 200
                      http.redirectcount.max: 0
                                qos.manifest: 100
                                 qos.content: 100
                               qos.aggregate: 100
                                   qos.level: 100

|mplane|
```
