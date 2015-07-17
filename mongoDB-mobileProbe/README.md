# MongoDB mobile Probe

## 1. Installation
----------------------------------------


Copy files from the mPlane interface (from the components GitHub) into protocol-ri/:
    - `mobile_probe_settings.json` The registry.json file, copy it into protocol-ri/mplane/components/.
    - `mongo.py` The Python interface, copy it into protocol-ri/mplane/components/.
    - `supervisor.conf` , `component.conf` and `client.conf` The configuration files, copy them into protocol-ri/conf/.


## 2. Configuration
----------------------------------------


The mongoDB proxy can be used by any component that has data stored in a mongoDB database. The configuration is given at a json file of the following format. 

```

 

{  
   "measurements":{  
      "mobile_probe_hardware":{  
         "collection":"mobileMeasurements",
         "search":"HW",
         "return":{  
            "observer.link":"HW.network_type",
            "snr":"HW.wifi_RSSI",
            "cpuload":"HW.Cpu Tot: ",
            "memload":"HW.MemFree"
         }
      },
      "mobile_probe_cellInfo":{  
         "collection":"mobileMeasurements",
         "search":"CELL_INFO",
         "return":{  
            "snr":"lCELL_INFO.atestGSMSignalStrength",
            "observer.link":"CELL_INFO.currentCellLocation"
         }
      },
      "mobile_probe_videoLog":{  
         "collection":"mobileMeasurements",
         "capability_name":"mobile_probe_videoLog",
         "search":"LogCat",
         "return":{  
            "measurement.identifier":"LogCat"
         }
      }
   },
   "collection":"mobileMeasurements",
   "db":"mPlane",
   "timestamp_field":"date",
   "source_filed":"deviceID"
}
```

The settings above will pull data from db mplane and collection mobileMeasurements. The field "devicID" will be used as the source field when making a query for a specific device. Furthermore, the timestamp field is "date"

The measurements dictionary contains information about the offered capabilities and the association of the return values between the mongoDB database and the mPlane reference implemenation. 
For instance, the mongoDB entry `HW.wifi_RSSI` will be returned as the mPlane's RI `snr` field.

The settings above will generate three capabilities. 

```
query (mobile_probe_hardware) 
query (mobile_probe_videoLog) 
query (mobile_probe_cellInfo)
```

## 3. Launching the probe
----------------------------------------

After installing the RI, in a terminal window start supervisor:

```
cd ~/protocol-ri
python3 -m scripts/mpsup --config ./conf/supervisor.conf
```

alternatively:

```
cd ~/protocol-ri 
python3 -m mplane.supervisor --config ./conf/supervisor.conf
```

In another terminal start the mobile probe as a component:

```
cd ~/protocol-ri 
python3 -m scripts/mpcom --config ./conf/component.conf 
```

The expected output for this example should be:
```
Added <Service for <capability: measure (ping-detail-ip4) when now ... future / 1s token c3877253 schema 5c73cc2a p/m/r 2/0/2>>
Added <Service for <capability: query (mobile_probe_hardware) when past ... now token f3a12891 schema 3673012f p/m/r 1/1/4>>
Added <Service for <capability: query (mobile_probe_videoLog) when past ... now token 57a0a948 schema d62c3d12 p/m/r 1/1/1>>
Added <Service for <capability: query (mobile_probe_cellInfo) when past ... now token cd6b5fa2 schema 0c9ed76a p/m/r 1/1/2>>

Capability registration outcome:
mobile_probe_hardware: Ok
mobile_probe_videoLog: Ok
mobile_probe_cellInfo: Ok

Checking for Specifications...
```


## 3. Launching an experiment
----------------------------------------
You need to have mongoDB setup and running on your machine. You should also have the settings.json configured in order to access and translate the mongoDB field into the mPlanes RI entries (see above). 

Start a client to test the component:

```
mpcli --config ./conf/client.conf
```
The expected output should be:
```
ok
mPlane client shell (rev 20.1.2015, sdk branch)
Type help or ? to list commands. ^D to exit.
```


Now check that the mongoDB capabilities is registered:
```
|mplane| listcap
Capability mobile_probe_cellInfo (token cd6b5fa2dc4ddfd3d7c4f16898bf1b60)
Capability mobile_probe_hardware (token f3a12891623783d20d4f63f01e86104d)
Capability mobile_probe_videoLog (token 57a0a9484788520090bf3e1c97aa6df8)
```

And run a test capability. In this example we ask for any mongoDB hardware entries for mobile device with IMEI 352605059221028 between 2013-09-20 and 2015-5-5: 

```
|mplane| runcap mobile_probe_hardware
|when| = 2013-09-20 ... 2015-5-5
source.device = 352605059221028
ok
```

If everything works ok the data should be pulled from the mongoDB database and transformed into an mPlane result: 
```
|mplane| listmeas
Result  mobile_probe_hardware-0 (token 6ed23ada2c8921f7cf9de917402a4283): 2015-03-31 11:19:58.851000 ... 2015-03-31 11:20:04.377000
```

You can now access the measurments:
```
|mplane| showmeas 6ed23ada2c8921f7cf9de917402a4283
result: query
    label       : mobile_probe_hardware-0
    token       : 6ed23ada2c8921f7cf9de917402a4283
    when        : 2015-03-31 11:19:58.851000 ... 2015-03-31 11:20:04.377000
    registry    : http://ict-mplane.eu/registry/demo
    parameters  ( 1): 
                           source.device: 352605059221028
    metadata    ( 1): 
                          System_version: 1.0
    resultvalues( 2):
          result 0:
                                     cpuload: 1.0
                                     memload: 20908.0
                               observer.link: WiFi
                                         snr: -37.0
          result 1:
                                     cpuload: 0.6805555820465088
                                     memload: 44084.0
                               observer.link: WiFi
                                         snr: -39.0

```
