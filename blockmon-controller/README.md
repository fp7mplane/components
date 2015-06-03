# Blockmon Controller

This is the interface of Blockmon controller to the mPlane SDK, which makes possible for an mPlane component to communicate with a Blockmon controller.

## Prerequisites

#### Blockmon Controller

The code for the Blockmon controller standalone version 
(required to run this program) is available on GitHub under [Blockmon controller](https://github.com/mdusi/blockmon-controller)

#### mPlane protocol Reference Implementation

The code for the mPlane protocol Reference Implementation (RI) is available on GitHub under [mPlane protocol RI](https://github.com/fp7mplane/protocol-ri)

## Howto

This howto assumes that [PROTOCOL_RI_DIR] is the folder where the GitHub repository of the mPlane protocol reference implementation has been cloned.

In order to have an mPlane-compliant version of the Blockmon controller, follow these steps.

1. Set the parameters in the file **blockmon-controller/blockmonController.conf** (e.g., path to certificates, supervisor address, client port and address, and roles)

2. Set the envirnoment variable MPLANE_RI to point to [PROTOCOL_RI_DIR]
	`
	
		$ export MPLANE_RI=[PROTOCOL_RI_DIR]
	`

3. Set the following parameters in the file **blockmon-controller/blockmonController.py** to connect to the Blockmon controller
	`
	
		_controller_address = Blockmon Controller address
		_controller_port = Blockmon Controller port
	`

4. Run Blockmon controller
	`
	
		$ python3 blockmonController.py --config blockmonController.conf
	`
