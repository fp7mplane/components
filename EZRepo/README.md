#EZRepo

[TOC]

###config (on the ocmponent side)
The URI must be given in the `component.conf` file under the component section. If no `registry_uri` is given no results are transmitted to the repo.

For the EZRepo no special configuration is needed.

Currently supported transport protocols:

 - UDP [`udp://<repo_ip>:<repo_port>`] - `udp://127.0.0.1:9900`

