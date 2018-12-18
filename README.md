# bgp_monitor

This is a simple BGP protocol monitoring tool with JSON REST API. 

It enables establishing a single BGP connection to a peer and monitor the advertised routes. It does not send out any Update BGP messages it only processes the ones sent by the far end peer.
To change the BGP peer address just edit the script.
This tool also provides a JSON REST API with three methods:

http://127.0.0.1:8000/count - that returns the number (an integer) of advertised prefixes;

http://127.0.0.1:8000/rib - that dump the RIB (Routing Information Base) in JSON format (see example output)

http://127.0.0.1:8000/prefix/192.168.0.1/32 - that queries the RIB checking if that specific prefix is being advertised (see example output).

You may edit the script to change the API port.

This script can be useful to monitor BGP activity and keep track of the number of known routes together with other tools like NAGIOS or Cacti. Be sure to test it out before setting up a BGP connection with a live router. 

I have used it so far with Cisco routers. Check the provided example configuration.




