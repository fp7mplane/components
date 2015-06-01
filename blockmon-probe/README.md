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

In order to have an mPlane-compliant version of the Blockmon node, follow these steps.

1. Set the parameters in the file **blockmon-probe/blockmon.conf** (e.g., path to certificates, supervisor address, client port and address, and roles)

2. Set the envirnoment variable MPLANE_RI to point to [PROTOCOL_RI_DIR]
	`
	
		$ export MPLANE_RI=[PROTOCOL_RI_DIR]
	`

3. Add a softlink to a working Blockmon standalone executable (e.g., to the folder [BLOCKMON_DIR])
	`
	
		$ cd blockmon-probe
		$ ln -s [BLOCKMON_DIR]/blockmon blockmon
	`

4. Run Blockmon probe (you might need administrative privileges if you capture from a network interface) 
	`
	
		$ python3 blockmon.py --config blockmon.conf
	`
