#EZRepo

###Good2Know
 - `component` supporting sending results to repository is only in SDK branch

###config
The URI must be given in the `component.conf` file under the component section. If no `registry_uri` is given no results are transmitted to the repo (no `registry_uri` should be given for the EZRepo component).

For the EZRepo no special configuration is needed, only the listening port(s) below the `component` section. If more ports are given, it must be weparated with a `,` (Whitespaces are not needed, but supported).
The `grading.json` is used for grading located under the mplane directory.

    [module_ezrepo]
    module = mplane.components.ezrepo
    port = <port1,port2>


Currently supported transport protocols for receiving results:

 - UDP [`udp://<repo_ip>:<repo_port>`] - `udp://127.0.0.1:9900`

###How2Use
Run an `EZRepo` component on a specific port. Start a `ping` component with the `registry_uri` containing the same port.
`EZRepo` will grade the received results, whose can be gathered via `ezrepo` capability.

TODO
 - threshold.json
 - grading
