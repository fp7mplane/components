### A preconfigured copy of mPlane SDK and mSLAcert is available on:

https://github.com/etego/msla

###Exmp of the network scenario: 
									PC2-Supervisor.py: 192.168.2.1
											|
											|
											|
											|
											|
									 _______|_________
									|				  |
									|				  |
PC1 - 192.168.1.1 <<<---------------   Networok	      ----------------->>>> PC4 - 192.168.4.1
mSLAcert_main.py					|		          |						mSLAcert_Agent.py
									|_________________|
											|
											|
											|
											|
											|
											|
								PC3-mPlane Clinet.py: 192.168.3.1

									
In base of you network configuration you have to change the seguent files, for the Ip and certificates:

./conf/client.conf
		[TLS]
		cert = PKI/ca/certs/"client-certicate".crt
		key = PKI/ca/certs/"plaintext certificate.key
		ca-chain = PKI/ca/root-ca/root-ca.crt

		[client]
		# leave registry_uri blank to use the default registry.json in the mplane/ folder
		registry_uri = 
		# http://ict-mplane.eu/registry/demo
		# workflow may be 'component-initiated' or 'client-initiated'
		workflow = component-initiated
		# for component-initiated:
		listen-host = "IP of the machine where is launched the client" (exmp:192.168.3.1)
		listen-port = 8891
		listen-spec-link = https://127.0.0.1:8891/
		registration-path = register/capability
		specification-path = show/specification
		result-path = register/result
		# for client-initiated:
		capability-url: "IP supervisor":8890/ (exmp:192.168.2.1:8890/)
		
./conf/component*.conf

		[TLS]
		cert = PKI/ca/certs/"Components-certicate".crt
		key = PKI/ca/certs/"plaintext certificate".key
		ca-chain = PKI/ca/root-ca/root-ca.crt

		[Roles]
		org.mplane.FUB.Clients.CI-Client_FUB = guest,admin
		"add also the roles for all the other components, client, supervisor ect"

		[Authorizations]
		msla-AGENT-Probe-ip4 = guest,admin
		"add the capability of your probe"

		[module_mSLA_main]
		module = mplane.components."name of python file"
		ip4addr = 1.2.3.4

		[component]
		scheduler_max_results = 20
		# leave registry_uri blank to use the default registry.json in the mplane/ folder
		registry_uri = 
		# http://ict-mplane.eu/registry/demo
		# workflow may be 'component-initiated' or 'client-initiated'
		workflow = component-initiated
		# for component-initiated
		client_host = "IP of the supervisor" (exmp: 192.168.2.1)
		client_port = 8889
		registration_path = register/capability
		specification_path = show/specification
		result_path = register/result
		# for client-initiated
		listen-port = 8888
		listen-cap-link = https://127.0.0.1:8888/

./conf/supervisor.conf

		[TLS]
		cert= PKI/ca/certs/CI-Supervisor-FUB.crt
		key= PKI/ca/certs/CI-Supervisor-FUB-plaintext.key
		ca-chain = PKI/ca/root-ca/root-ca.crt

		[Roles]
		org.mplane.FUB.Components.mSLAcert_server = guest,admin
		org.mplane.FUB.Agent.mSLAcert_Agent = guest,admin
		org.mplane.FUB.Supervisors.CI_Supervisor_FUB = admin
		Supervisor-1.FUB.mplane.org = admin
		org.mplane.FUB.Clients.CI-Client_FUB = guest,admin


		[Authorizations]
		ping-average-ip4 = guest,admin
		ping-detail-ip4 = guest,admin
		tcpsla-average-ip4 = guest,admin
		tcpsla-detail-ip4 = guest,admin
		udpsla-average-ip4 = guest,admin
		udpsla-detail-ip4 = guest,admin
		msla-average-ip4 = guest,admin
		msla-detail-ip4 = guest,admin
		msla-AGENT-Probe-ip4 = guest,admin

		[client]
		# workflow may be 'component-initiated' or 'client-initiated'
		workflow = component-initiated
		# for component-initiated:
		listen-host = "IP of the machine where is launched the supervisor" (exmp: 192.168.2.1)
		listen-port = 8889
		listen-spec-link = 
		# https://127.0.0.1:8889/
		registration-path = register/capability
		specification-path = show/specification
		result-path = register/result
		# for client-initiated:
		component-urls: "IP of component 1":8888/,"IP of component 2":8888/ (exmp: 192.168.1.1:8888/,192.168.4.1:8888/)

		[component]
		scheduler_max_results = 20
		# leave registry_uri blank to use the default registry.json in the mplane/ folder
		registry_uri = 
		# http://ict-mplane.eu/registry/demo
		# workflow may be 'component-initiated' or 'client-initiated'
		workflow = component-initiated
		# for component-initiated:
		client_host = "IP of the machine where is launched the client" (exmp: 192.168.2.1)
		client_port = 8891 / 9911
		registration_path = register/capability
		specification_path = show/specification
		result_path = register/result
		# for client-initiated:
		listen-port = 8890
		listen-cap-link = 
		# https://127.0.0.1:8890/

###To generate certificates use the scripts from mPlane RI (https://github.com/fp7mplane/protocol-ri)

	./PKI/create_client_cert.sh
	./PKI/create_component_cert.sh
	./PKI/create_supervisor_cert.sh
	"follow instruction on ./PKI/HOWTO.txt"

### Additional configuration
mSLAcert uses Iperf to generate traffic, the traffic flows from mSLAcert_main to mSLAcert_Agent.
For TCP traffic is used port 5001, and for UDP traffic port 5002. 
When using NAT remeber to use port forwarding for the one configured above, 
if you want you can change the ports 5001 and 5002 from the mSLAcert_main.py and mSLAcert_Agent.py

### HOWTO run for mSLAcert with component-initiated workflow, run in this order:

>>>To run the CI components (with SSL), from the protocol-ri directory, run:

>>>To run CI mSLAcert server:

```export PYTHONPATH=.```

```./scripts/mpcom --config ./conf/component.conf```



>>>To run CI mSLAcert Agent:

```export PYTHONPATH=.```

```./scripts/mpcom --config ./conf/component-agent.conf```



>>>To run mPlane client:

```export PYTHONPATH=.```

```./scripts/mpcli --config ./conf/client.conf```


>>>End the supoervisor in the end:

```export PYTHONPATH=.```

```./scripts/mpsup --config ./conf/supervisor.conf```


This will launch the supervisor. 
###Then from the client:
1. to view the cap to run
		listcap
2. Run capability
		runcap
3. set the period
		now + 40s / 1s
4. set a different time
		when now + 34s / 1s
5. do a new measurement for the same capability and destination
		set destination.ip4 x.x.x.x

