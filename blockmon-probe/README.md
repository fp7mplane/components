# Blockmon probe

This is the interface of Blockmon probe to the mPlane SDK, which makes possible for a Blockmon node to communicate with other mPlane components.

## Prerequisites

#### Blockmon node

The code for the Blockmon probe standalone version 
(required to run this program) is available on GitHub under [Blockmon node](https://github.com/blockmon/blockmon)

#### mPlane protocol Reference Implementation

The code for the mPlane protocol Reference Implementation (RI) is available on GitHub under [mPlane protocol RI](https://github.com/fp7mplane/protocol-ri)

## Howto

This howto assumes that 

* [BLOCKMON_DIR] is the folder where the GitHub repository of the Blockmon node standalone version has been cloned;
* [PROTOCOL_RI_DIR] is the folder where the GitHub repository of the mPlane protocol reference implementation has been cloned;
* [COMPONENTS_DIR] is the folder where the GitHub repository of the components (this repository) has been cloned;
* [PROTOCOL_RI_DIR] is the current working directory.

In order to have an mPlane-compliant version of the Blockmon node, follow these steps.

1. Add the Blockmon component and its capabilities to the protocol RI, inside the corresponding sections in the file **conf/component.conf**
	`
	
		[Authorizations]	
		blockmon-packets = guest,admin
		blockmon-flows = guest,admin
		blockmon-flows-tcp = guest,admin
		blockmon-tstat = guest,admin
		
		[module_blockmon]
		module = mplane.components.blockmon
	`

2. Add the Blockmon capabilities to the supervisor of the protocol RI, inside the corresponding sections in the file **conf/supervisor.conf**
	`
	
		[Authorizations]	
		blockmon-packets = guest,admin
		blockmon-flows = guest,admin
		blockmon-flows-tcp = guest,admin
		blockmon-tstat = guest,admin
	`

3. Add a softlink to a working Blockmon standalone executable (e.g., in the folder [BLOCKMON_DIR])
	`
	
		$ ln -s [BLOCKMON_DIR]/blockmon blockmon
	`
4. Add a softlink to Blockmon capabilities and to the blockmon.py component
	`
	
		$ ln -s [COMPONENTS_DIR]/components/blockmon-probe/capabilities capabilities
		$ cd mplane/components
		$ ln -s [COMPONENTS_DIR]/components/blockmon-probe/blockmon.py blockmon.py
		$ cd [PROTOCOL_RI_DIR]
	`

5. In order for the example capabilities to work, it is useful to have a softlink to a sample pcap
	`
	
		$ ln -s [SAMPLES]/sample.pcap sample.pcap
	`
