#EZRepo

###Good2Know
 - `component` supporting sending results to repository is only in SDK branch

###config (on the ocmponent side)
The URI must be given in the `component.conf` file under the component section. If no `registry_uri` is given no results are transmitted to the repo (no `registry_uri` should be given for the EZRepo component).

For the EZRepo no special configuration is needed, only the listening port below the `component` section:

    [module_ezrepo]
    module = mplane.components.ezrepo
    port = 9900


Currently supported transport protocols:

 - UDP [`udp://<repo_ip>:<repo_port>`] - `udp://127.0.0.1:9900`

