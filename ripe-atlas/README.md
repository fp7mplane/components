# Ripe Atlas

This component integrates the Atlas Toolbox (https://github.com/pierdom/atlas-toolbox), 
a collection of Perl command-line scripts from managing custom User Defined Measurements (UDMs) 
on the RIPE Atlas network.

## 1. Installation
---------------------------------------

- Copy files from the mPlane interface (from the components GitHub) into protocol-ri/:
- Copy the 'registry.json' file into protocol-ri/mplane/components/
- Copy 'supervisor.conf' , 'component.conf' and 'client.conf' into protocol-ri/conf/
- Clone repository https://github.com/pierdom/atlas-toolbox.git into mplane/components/ripe-atlas
- Install atlas-toolbox (follow steps reported on https://github.com/pierdom/atlas-toolbox.git)

## 2. Configuring database

The component can produce output to a PostgreSQL database, to do that the parameter db_connect_params
needs to be correctly set as a dsn parameter indicating the database to connect to (http://initd.org/psycopg/docs/module.html).
For example to connect to a local database called "dbstream" available at port 5432 with user "mplane" password "123":

```
db_connect_params = dbname=dbstream port=5432 user=mplane password=123
```
Please note that to run the Postgres database locally you need to change the default config option in pg_hba.conf line:

from

```
# TYPE DATABASE USER ADDRESS METHOD
local  all      all          peer
```

to

```
# TYPE DATABASE USER ADDRESS METHOD
local  all      all          md5
```

After this you'll need to restart PostgreSQL if it's running. E.g. sudo service postgresql restart

The results will be stored in a table called ripe_results that needs to be created in the designated database.
Just connect to the database:

```
psql -p 5432 -d dbstream -U mplane -W
```
And give the command:

```
\i ripe_result.sql
```

## 3. Running Probe
---------------------------------------

After installing the RI, in a terminal window start supervisor:

```
export PYTHONPATH=.
cd ~/protocol-ri
python3 -m scripts/mpsup --config ./conf/supervisor.conf
```

In another terminal start the mobile probe as a component:

```
export PYTHONPATH=.
cd ~/protocol-ri 
python3 -m scripts/mpcom --config ./conf/component.conf 
```

The expected output for this example should be:

```
Added <Service for <capability: measure (ripeatlas-list-probe) when now token 3599914c schema 74498fe8 p/m/r 1/0/1>>
Added <Service for <capability: measure (ripeatlas-udm-lookup) when now token 346d14a5 schema 615bd7f6 p/m/r 1/0/1>>
Added <Service for <capability: measure (ripeatlas-udm-create) when now token 077743d8 schema 5d8958c9 p/m/r 1/0/1>>
Added <Service for <capability: measure (ripeatlas-udm-status) when now token d22e070a schema d416e623 p/m/r 1/0/1>>
Added <Service for <capability: measure (ripeatlas-udm-result) when now token 3725aaab schema 0c0adf42 p/m/r 1/0/1>>
Added <Service for <capability: measure (ripeatlas-udm-stop) when now token 4a50355e schema a8992e4b p/m/r 1/0/1>>

Capability registration outcome:
ripeatlas-udm-lookup: Ok
ripeatlas-udm-status: Ok
ripeatlas-udm-stop: Ok
ripeatlas-udm-result: Ok
callback: Ok
ripeatlas-list-probe: Ok
ripeatlas-udm-create: Ok

Checking for Specifications...
```

## 4. Using RipeAtlas through ri-protocol
---------------------------------------

Start a client to test the component:

```
export PYTHONPATH=.
mpcli --config ./conf/client.conf
```

The expected output should be:

```
ok
mPlane client shell (rev 20.1.2015, sdk branch)
Type help or ? to list commands. ^D to exit.
```

Now check that the capabilities are registered:

```
|mplane| listcap
Capability ripeatlas-list-probe (token 3599914c02c1aacfe495a6cc4716afa6)
Capability ripeatlas-udm-create (token 077743d8b6bcce9733e979ce183d3630)
Capability ripeatlas-udm-lookup (token 346d14a54d51b5cf9b183be86c92d768)
Capability ripeatlas-udm-result (token 3725aaaba620561d179b829c1e778d61)
Capability ripeatlas-udm-status (token d22e070a7132e32be7a06c1952780943)
Capability ripeatlas-udm-stop (token 4a50355ec074cbf1006f983333343ffa)
```

Run a test capability. In this example, we first retrieve a set of probes, then instruct a subset of these probes to perform a ping to www.google.com and collect the result.
For a complete description of the RIPE atlas toolbox, please refer to https://github.com/pierdom/atlas-toolbox

Step 1, list a set of probes: find all probes in Italy at less than 2Km from an address:

```
|mplane| runcap ripeatlas-list-probe
|when| = now
ripeatlas.optionsline = --country it --address "Piazza di Spagna, Rome" --radius 2
ok
|mplane| listmeas
Result  ripeatlas-list-probe-0 (token fb2c03ae6f46400c07cbfa5a17df82dd): 2015-09-02 15:00:05.883059
|mplane| showmeas ripeatlas-list-probe-0
result: measure
    label       : ripeatlas-list-probe-0
    token       : fb2c03ae6f46400c07cbfa5a17df82dd
    when        : 2015-09-02 15:00:05.883059
    registry    : http://ict-mplane.eu/registry/core
    parameters  ( 1): 
                   ripeatlas.optionsline: --country it --address "Piazza di Spagna, Rome" --radius 2
    resultvalues( 7):
          result 0:
             ripeatlas.list.probe.resultline: 249	193.206.159.174	193.206.0.0/16	137	IT	41.8915	12.4895	1

          result 1:
             ripeatlas.list.probe.resultline: 1447	2.231.3.243	2.224.0.0/13	12874	IT	41.8905	12.4795	1

          result 2:
             ripeatlas.list.probe.resultline: 11877	31.31.44.70	31.31.40.0/21	57329	IT	41.9005	12.5005	1

          result 3:
             ripeatlas.list.probe.resultline: 15878	79.60.56.81	79.60.0.0/16	3269	IT	41.8915	12.4705	1

          result 4:
             ripeatlas.list.probe.resultline: 18350	94.37.58.70	94.36.0.0/14	8612	IT	41.9075	12.4595	1

          result 5:
             ripeatlas.list.probe.resultline: 20259	NA	217.12.128.0/20	12559	IT	41.9015	12.4995	1

          result 6:
             ripeatlas.list.probe.resultline: 22094	151.24.148.182	151.24.0.0/16	1267	IT	41.8995	12.5015	1
```

Step 2, use probes 22094 15878 and 249 to perform a ping to www.google.com (Note that you need to provide an API key with 'Measurement creation' permissions):

```
|mplane| set ripeatlas.optionsline --api xxxxxx --target www.google.com --probe-list 22094,15878,249 --type ping
ripeatlas.optionsline = --api xxxxx --target www.google.com --probe-list 22094,15878,249 --type ping
|mplane| runcap ripeatlas-udm-create
ok
|mplane| showmeas ripeatlas-udm-create-1
result: measure
    label       : ripeatlas-udm-create-1
    token       : 211f33e24c40f2cb3844c17343656b5d
    when        : 2015-09-02 15:07:56.707434
    registry    : http://ict-mplane.eu/registry/core
    parameters  ( 1): 
                   ripeatlas.optionsline: --api xxxxx --target www.google.com --probe-list 22094,15878,249 --type ping
    resultvalues( 1):
          result 0:
             ripeatlas.udm.create.resultline: 2374961
```

The ripeatlas-udm-create capability returns a udm code: 2374961 that we can use to manage the measure.

Step 3, get the result for the measurement:

```
|mplane| set ripeatlas.optionsline --udm 2374961 --api xxxxx
ripeatlas.optionsline = --udm 2374961 --api xxxxx
|mplane| runcap ripeatlas-udm-result
ok
|mplane| showmeas ripeatlas-udm-result-3
result: measure
    label       : ripeatlas-udm-result-3
    token       : a560ab1903abf9bee6a92272121c294c
    when        : 2015-09-02 15:13:19.564349
    registry    : http://ict-mplane.eu/registry/core
    parameters  ( 1): 
                   ripeatlas.optionsline: --udm 2374961 --api xxxxx
    resultvalues( 9):
          result 0:
             ripeatlas.udm.result.resultline: 1441206482	15878	79.60.56.81	64.233.167.147	64.233.167.147	42.393

          result 1:
             ripeatlas.udm.result.resultline: 1441206482	15878	79.60.56.81	64.233.167.147	64.233.167.147	37.595

          result 2:
             ripeatlas.udm.result.resultline: 1441206482	15878	79.60.56.81	64.233.167.147	64.233.167.147	38.227

          result 3:
             ripeatlas.udm.result.resultline: 1441206482	22094	151.24.148.182	64.233.167.147	64.233.167.147	33.793

          result 4:
             ripeatlas.udm.result.resultline: 1441206482	22094	151.24.148.182	64.233.167.147	64.233.167.147	34.553

          result 5:
             ripeatlas.udm.result.resultline: 1441206482	22094	151.24.148.182	64.233.167.147	64.233.167.147	34.045

          result 6:
             ripeatlas.udm.result.resultline: 1441206484	249	193.206.159.174	64.233.167.147	64.233.167.147	28.604

          result 7:
             ripeatlas.udm.result.resultline: 1441206484	249	193.206.159.174	64.233.167.147	64.233.167.147	28.398

          result 8:
             ripeatlas.udm.result.resultline: 1441206484	249	193.206.159.174	64.233.167.147	64.233.167.147	29.025
```

Each result is a ping measurement, the columns definition is the following:
timestamp | probe_id | probe_ip | dst_name | dst_addr | rtt

The values of the ping are therefore 42.393, 37.595, ..., 29.025

If the database connection is correctly configured, then all the results will be also stored in a database table called ripe_results.
For example, the above mentioned commands, would give as a final result in the database:

```
        serial_time         |       capability       | measure_number |                                     result                                     
----------------------------+------------------------+----------------+--------------------------------------------------------------------------------
 2015-09-03 15:32:54.475757 | ripeatlas-list-probe-1 |              0 | 249     193.206.159.174 193.206.0.0/16  137     IT      41.8915 12.4895 1
 2015-09-03 15:32:54.475757 | ripeatlas-list-probe-1 |              1 | 1447    2.231.3.243     2.224.0.0/13    12874   IT      41.8905 12.4795 1
 2015-09-03 15:32:54.475757 | ripeatlas-list-probe-1 |              2 | 11877   31.31.44.70     31.31.40.0/21   57329   IT      41.9005 12.5005 1
 2015-09-03 15:32:54.475757 | ripeatlas-list-probe-1 |              3 | 15878   79.60.56.81     79.60.0.0/16    3269    IT      41.8915 12.4705 1
 2015-09-03 15:32:54.475757 | ripeatlas-list-probe-1 |              4 | 18350   94.37.58.70     94.36.0.0/14    8612    IT      41.9075 12.4595 1
 2015-09-03 15:32:54.475757 | ripeatlas-list-probe-1 |              5 | 20259   NA      217.12.128.0/20 12559   IT      41.9015 12.4995 1
 2015-09-03 15:32:54.475757 | ripeatlas-list-probe-1 |              6 | 22094   151.24.148.182  151.24.0.0/16   1267    IT      41.8995 12.5015 1
 2015-09-03 15:37:10.422271 | ripeatlas-udm-create-3 |              0 | 2382480
 2015-09-03 15:38:10.55785  | ripeatlas-udm-result-4 |              0 | 1441294637      249     193.206.159.174 173.194.67.147  173.194.67.147  30.715
 2015-09-03 15:38:10.55785  | ripeatlas-udm-result-4 |              1 | 1441294637      249     193.206.159.174 173.194.67.147  173.194.67.147  30.526
 2015-09-03 15:38:10.55785  | ripeatlas-udm-result-4 |              2 | 1441294637      249     193.206.159.174 173.194.67.147  173.194.67.147  30.5
```

