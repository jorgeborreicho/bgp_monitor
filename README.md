# bgp_monitor

This is a simple BGP protocol monitoring tool with JSON REST API. 

It enables establishing a single BGP connection to a peer and monitor the advertised routes. It does not send out any Update BGP messages it only processes the ones sent by the far end peer.
To change the BGP peer address just edit the script.
This tool also provides a JSON REST API with three methods:

http://127.0.0.1:8000/count - that returns the number (an integer) of advertised prefixes;

http://127.0.0.1:8000/rib - that dump the RIB (Routing Information Base) in JSON format;

http://127.0.0.1:8000/prefix/192.168.0.1/32 - that queries the RIB checking if that specific prefix is being advertised.

You may edit the script to change the API port.
This script can be useful to monitor BGP activity and keep track of the number of known routes together with other tools like NAGIOS or Cacti. Be sure to test it out before setting up a BGP connection with a live router. 

I have used it so far with Cisco routers. 

Example Cisco configuration:

!
interface Loopback0
 ip address 192.168.0.1 255.255.255.255
!
interface Loopback1
 ip address 192.168.1.1 255.255.255.255
!
interface Loopback2
 ip address 192.168.2.1 255.255.255.255
!
interface FastEthernet0/0
 ip address 10.10.1.2 255.255.255.0
 duplex auto
 speed auto
!
interface FastEthernet0/1
 no ip address
 shutdown
 duplex auto
 speed auto
!
router bgp 65000
 bgp log-neighbor-changes
 neighbor 10.10.1.1 remote-as 65001
 default-metric 20
 !
 address-family ipv4
  redistribute connected
  neighbor 10.10.1.1 activate
  neighbor 10.10.1.1 send-community
  neighbor 10.10.1.1 soft-reconfiguration inbound
  neighbor 10.10.1.1 route-map EXPORT1 out
  default-metric 20
  no auto-summary
  no synchronization
 exit-address-family
!
access-list 1 permit 192.168.0.1 log
no cdp log mismatch duplex
!
route-map EXPORT1 permit 10
 match ip address 1
 set metric 100
 set as-path prepend 10 20 30
 set community 45940737 45941236 45941237
!
route-map EXPORT1 permit 20
 description default-rule
!
!





