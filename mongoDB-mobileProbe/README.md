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

In another terminal start the anycast probe as a component:

```
cd ~/protocol-ri 
python3 -m scripts/mpcom --config ./conf/anycast.conf
```

<capability: measure (callback) when now ... future token c855a414 schema a7b45ce6 p/m/r 0/0/0>>
```

## 3. Launching an experiment
----------------------------------------
