# marpla-dc-1-s01

## Table of Contents

- [Management](#management)
  - [Management Interfaces](#management-interfaces)
  - [DNS Domain](#dns-domain)
  - [IP Name Servers](#ip-name-servers)
  - [Domain Lookup](#domain-lookup)
  - [NTP](#ntp)
  - [Management API HTTP](#management-api-http)
- [Authentication](#authentication)
  - [Local Users](#local-users)
  - [Enable Password](#enable-password)
- [Monitoring](#monitoring)
  - [TerminAttr Daemon](#terminattr-daemon)
- [Internal VLAN Allocation Policy](#internal-vlan-allocation-policy)
  - [Internal VLAN Allocation Policy Summary](#internal-vlan-allocation-policy-summary)
  - [Internal VLAN Allocation Policy Device Configuration](#internal-vlan-allocation-policy-device-configuration)
- [VLANs](#vlans)
  - [VLANs Summary](#vlans-summary)
  - [VLANs Device Configuration](#vlans-device-configuration)
- [Interfaces](#interfaces)
  - [Ethernet Interfaces](#ethernet-interfaces)
  - [Loopback Interfaces](#loopback-interfaces)
  - [VLAN Interfaces](#vlan-interfaces)
  - [VXLAN Interface](#vxlan-interface)
- [Routing](#routing)
  - [Service Routing Protocols Model](#service-routing-protocols-model)
  - [Virtual Router MAC Address](#virtual-router-mac-address)
  - [IP Routing](#ip-routing)
  - [IPv6 Routing](#ipv6-routing)
  - [Static Routes](#static-routes)
  - [Router BGP](#router-bgp)
- [BFD](#bfd)
  - [Router BFD](#router-bfd)
- [Multicast](#multicast)
  - [IP IGMP Snooping](#ip-igmp-snooping)
- [Filters](#filters)
  - [Prefix-lists](#prefix-lists)
  - [Route-maps](#route-maps)
- [VRF Instances](#vrf-instances)
  - [VRF Instances Summary](#vrf-instances-summary)
  - [VRF Instances Device Configuration](#vrf-instances-device-configuration)

## Management

### Management Interfaces

#### Management Interfaces Summary

##### IPv4

| Management Interface | Description | Type | VRF | IP Address | Gateway |
| -------------------- | ----------- | ---- | --- | ---------- | ------- |
| Management1 | OOB_MANAGEMENT | oob | MGMT | 10.30.11.1/16 | 10.30.0.1 |

##### IPv6

| Management Interface | Description | Type | VRF | IPv6 Address | IPv6 Gateway | ND RA Disabled | ND RA RX Accept | ND Managed Config Flag | ND Other Config Flag | ND Cache | ND RA DNS Servers |
| -------------------- | ----------- | ---- | --- | ------------ | ------------ | -------------- | --------------- | ---------------------- | -------------------- | -------- | ----------------- |
| Management1 | OOB_MANAGEMENT | oob | MGMT | - | - | - | - | - | - | - | - |

#### Management Interfaces Device Configuration

```eos
!
interface Management1
   description OOB_MANAGEMENT
   no shutdown
   vrf MGMT
   ip address 10.30.11.1/16
```

### DNS Domain

DNS domain: avd.lab

#### DNS Domain Device Configuration

```eos
dns domain avd.lab
!
```

### IP Name Servers

#### IP Name Servers Summary

| Name Server | VRF | Priority |
| ----------- | --- | -------- |
| 8.8.8.8 | MGMT | - |

#### IP Name Servers Device Configuration

```eos
ip name-server vrf MGMT 8.8.8.8
```

### Domain Lookup

#### DNS Domain Lookup Summary

| Source interface | vrf |
| ---------------- | --- |
| Management1 | MGMT |

#### DNS Domain Lookup Device Configuration

```eos
ip domain lookup vrf MGMT source-interface Management1
```

### NTP

#### NTP Summary

##### NTP Local Interface

| Interface | VRF |
| --------- | --- |
| Management1 | MGMT |

##### NTP Servers

NTP servers VRF: MGMT

| Server | Preferred | Burst | iBurst | Version | Min Poll | Max Poll | Local-interface | Source Address | Key |
| ------ | --------- | ----- | ------ | ------- | -------- | -------- | --------------- | -------------- | --- |
| time.apple.com | - | - | - | - | - | - | - | - | - |
| time.google.com | True | - | - | - | - | - | - | - | - |
| time.windows.com | - | - | - | - | - | - | - | - | - |

#### NTP Device Configuration

```eos
!
ntp local-interface vrf MGMT Management1
ntp server vrf MGMT time.apple.com
ntp server vrf MGMT time.google.com prefer
ntp server vrf MGMT time.windows.com
```

### Management API HTTP

#### Management API HTTP Summary

| HTTP | HTTPS | UNIX-Socket | Default Services | Session Timeout |
| ---- | ----- | ----------- | ---------------- | --------------- |
| False | True | - | - | 1440 minutes |

#### Management API VRF Access

| VRF Name | IPv4 ACL | IPv6 ACL |
| -------- | -------- | -------- |
| MGMT | - | - |

#### Management API HTTP Device Configuration

```eos
!
management api http-commands
   protocol https
   no protocol http
   no shutdown
   !
   vrf MGMT
      no shutdown
```

## Authentication

### Local Users

#### Local Users Summary

| User | Privilege | Role | Disabled | Shell |
| ---- | --------- | ---- | -------- | ----- |
| arista | 15 | network-admin | False | - |

#### Local Users Device Configuration

```eos
!
username arista privilege 15 role network-admin secret sha512 <removed>
```

### Enable Password

Enable password has been disabled

## Monitoring

### TerminAttr Daemon

#### TerminAttr Daemon Summary

| CV Compression | CloudVision Servers | VRF | Authentication | Smash Excludes | Ingest Exclude | Bypass AAA |
| -------------- | ------------------- | --- | -------------- | -------------- | -------------- | ---------- |
| gzip | apiserver.cv-prod-euwest-2.arista.io:443 | MGMT | token-secure,/mnt/flash/cv-onboarding-token | ale,flexCounter,hardware,kni,pulse,strata | /Sysdb/cell/1/agent,/Sysdb/cell/2/agent | True |

#### TerminAttr Daemon Device Configuration

```eos
!
daemon TerminAttr
   exec /usr/bin/TerminAttr -cvaddr=apiserver.cv-prod-euwest-2.arista.io:443 -cvauth=token-secure,/mnt/flash/cv-onboarding-token -cvvrf=MGMT -disableaaa -smashexcludes=ale,flexCounter,hardware,kni,pulse,strata -ingestexclude=/Sysdb/cell/1/agent,/Sysdb/cell/2/agent -taillogs
   no shutdown
```

## Internal VLAN Allocation Policy

### Internal VLAN Allocation Policy Summary

| Policy Allocation | Range Beginning | Range Ending |
| ----------------- | --------------- | ------------ |
| ascending | 1006 | 1199 |

### Internal VLAN Allocation Policy Device Configuration

```eos
!
vlan internal order ascending range 1006 1199
```

## VLANs

### VLANs Summary

| VLAN ID | Name | Trunk Groups |
| ------- | ---- | ------------ |
| 110 | EXT_FW | - |
| 210 | WEW_FW | - |
| 310 | PRIV_FW | - |
| 399 | FW_HA | - |

### VLANs Device Configuration

```eos
!
vlan 110
   name EXT_FW
!
vlan 210
   name WEW_FW
!
vlan 310
   name PRIV_FW
!
vlan 399
   name FW_HA
```

## Interfaces

### Ethernet Interfaces

#### Ethernet Interfaces Summary

##### L2

| Interface | Description | Mode | VLANs | Native VLAN | Trunk Group | Channel-Group |
| --------- | ----------- | ---- | ----- | ----------- | ----------- | ------------- |

*Inherited from Port-Channel Interface

##### IPv4

| Interface | Description | Channel Group | IP Address | VRF | MTU | Shutdown | ACL In | ACL Out |
| --------- | ----------- | ------------- | ---------- | --- | --- | -------- | ------ | ------- |
| Ethernet1 | P2P_marpla-dc-1-wew-l01_Ethernet1 | - | 10.101.10.0/31 | default | 9214 | False | - | - |
| Ethernet2 | P2P_marpla-dc-1-wew-l02_Ethernet1 | - | 10.101.10.4/31 | default | 9214 | False | - | - |
| Ethernet3 | P2P_marpla-dc-1-priv-l03_Ethernet1 | - | 10.101.10.8/31 | default | 9214 | False | - | - |
| Ethernet4 | P2P_marpla-dc-1-priv-l04_Ethernet1 | - | 10.101.10.12/31 | default | 9214 | False | - | - |
| Ethernet5 | P2P_marpla-dc-1-ext-l05_Ethernet1 | - | 10.101.10.16/31 | default | 9214 | False | - | - |
| Ethernet6 | P2P_marpla-dc-1-ext-l06_Ethernet1 | - | 10.101.10.20/31 | default | 9214 | False | - | - |
| Ethernet7 | DCI_marpla-dc-2-s01_Ethernet7 | - | 10.100.0.0/31 | default | 9214 | False | - | - |
| Ethernet8 | DCI_marpla-dc-2-s02_Ethernet8 | - | 10.100.0.2/31 | default | 9214 | False | - | - |

#### Ethernet Interfaces Device Configuration

```eos
!
interface Ethernet1
   description P2P_marpla-dc-1-wew-l01_Ethernet1
   no shutdown
   mtu 9214
   no switchport
   ip address 10.101.10.0/31
!
interface Ethernet2
   description P2P_marpla-dc-1-wew-l02_Ethernet1
   no shutdown
   mtu 9214
   no switchport
   ip address 10.101.10.4/31
!
interface Ethernet3
   description P2P_marpla-dc-1-priv-l03_Ethernet1
   no shutdown
   mtu 9214
   no switchport
   ip address 10.101.10.8/31
!
interface Ethernet4
   description P2P_marpla-dc-1-priv-l04_Ethernet1
   no shutdown
   mtu 9214
   no switchport
   ip address 10.101.10.12/31
!
interface Ethernet5
   description P2P_marpla-dc-1-ext-l05_Ethernet1
   no shutdown
   mtu 9214
   no switchport
   ip address 10.101.10.16/31
!
interface Ethernet6
   description P2P_marpla-dc-1-ext-l06_Ethernet1
   no shutdown
   mtu 9214
   no switchport
   ip address 10.101.10.20/31
!
interface Ethernet7
   description DCI_marpla-dc-2-s01_Ethernet7
   no shutdown
   mtu 9214
   no switchport
   ip address 10.100.0.0/31
!
interface Ethernet8
   description DCI_marpla-dc-2-s02_Ethernet8
   no shutdown
   mtu 9214
   no switchport
   ip address 10.100.0.2/31
```

### Loopback Interfaces

#### Loopback Interfaces Summary

##### IPv4

| Interface | Description | VRF | IP Address |
| --------- | ----------- | --- | ---------- |
| Loopback0 | ROUTER_ID | default | 10.101.0.1/32 |
| Loopback1 | VXLAN_TUNNEL_SOURCE | default | 10.101.3.1/32 |

##### IPv6

| Interface | Description | VRF | IPv6 Addresses |
| --------- | ----------- | --- | -------------- |
| Loopback0 | ROUTER_ID | default | - |
| Loopback1 | VXLAN_TUNNEL_SOURCE | default | - |

#### Loopback Interfaces Device Configuration

```eos
!
interface Loopback0
   description ROUTER_ID
   no shutdown
   ip address 10.101.0.1/32
!
interface Loopback1
   description VXLAN_TUNNEL_SOURCE
   no shutdown
   ip address 10.101.3.1/32
```

### VLAN Interfaces

#### VLAN Interfaces Summary

| Interface | Description | VRF | MTU | Shutdown |
| --------- | ----------- | --- | --- | -------- |
| Vlan110 | EXT_FW | EXT | - | False |
| Vlan210 | WEW_FW | WEW | - | False |
| Vlan310 | PRIV_FW | PRIV | - | False |

##### IPv4

| Interface | VRF | IP Address | IP Address Virtual | IP Router Virtual Address | ACL In | ACL Out |
| --------- | --- | ---------- | ------------------ | ------------------------- | ------ | ------- |
| Vlan110 | EXT | - | 10.1.10.1/24 | - | - | - |
| Vlan210 | WEW | - | 10.2.10.1/24 | - | - | - |
| Vlan310 | PRIV | - | 10.3.10.1/24 | - | - | - |

#### VLAN Interfaces Device Configuration

```eos
!
interface Vlan110
   description EXT_FW
   no shutdown
   vrf EXT
   ip address virtual 10.1.10.1/24
!
interface Vlan210
   description WEW_FW
   no shutdown
   vrf WEW
   ip address virtual 10.2.10.1/24
!
interface Vlan310
   description PRIV_FW
   no shutdown
   vrf PRIV
   ip address virtual 10.3.10.1/24
```

### VXLAN Interface

#### VXLAN Interface Summary

| Setting | Value |
| ------- | ----- |
| Source Interface | Loopback1 |
| UDP port | 4789 |

##### VLAN to VNI, Flood List and Multicast Group Mappings

| VLAN | VNI | Flood List | Multicast Group |
| ---- | --- | ---------- | --------------- |
| 110 | 1000110 | - | - |
| 210 | 2000210 | - | - |
| 310 | 3000310 | - | - |
| 399 | 3000399 | - | - |

##### VRF to VNI and Multicast Group Mappings

| VRF | VNI | Overlay Multicast Group to Encap Mappings |
| --- | --- | ----------------------------------------- |
| EXT | 1009000 | - |
| PRIV | 3009000 | - |
| WEW | 2009000 | - |

#### VXLAN Interface Device Configuration

```eos
!
interface Vxlan1
   description marpla-dc-1-s01_VTEP
   vxlan source-interface Loopback1
   vxlan udp-port 4789
   vxlan vlan 110 vni 1000110
   vxlan vlan 210 vni 2000210
   vxlan vlan 310 vni 3000310
   vxlan vlan 399 vni 3000399
   vxlan vrf EXT vni 1009000
   vxlan vrf PRIV vni 3009000
   vxlan vrf WEW vni 2009000
```

## Routing

### Service Routing Protocols Model

Multi agent routing protocol model enabled

```eos
!
service routing protocols model multi-agent
```

### Virtual Router MAC Address

#### Virtual Router MAC Address Summary

Virtual Router MAC Address: 00:1c:73:00:dc:99

#### Virtual Router MAC Address Device Configuration

```eos
!
ip virtual-router mac-address 00:1c:73:00:dc:99
```

### IP Routing

#### IP Routing Summary

| VRF | Routing Enabled |
| --- | --------------- |
| default | True |
| EXT | True |
| MGMT | False |
| PRIV | True |
| WEW | True |

#### IP Routing Device Configuration

```eos
!
ip routing
ip routing vrf EXT
no ip routing vrf MGMT
ip routing vrf PRIV
ip routing vrf WEW
```

### IPv6 Routing

#### IPv6 Routing Summary

| VRF | Routing Enabled |
| --- | --------------- |
| default | False |
| EXT | False |
| MGMT | False |
| PRIV | False |
| WEW | False |

### Static Routes

#### Static Routes Summary

| VRF | Destination Prefix | Next Hop IP | Exit interface | Administrative Distance | Tag | Route Name | Metric |
| --- | ------------------ | ----------- | -------------- | ----------------------- | --- | ---------- | ------ |
| MGMT | 0.0.0.0/0 | 10.30.0.1 | - | 1 | - | - | - |

#### Static Routes Device Configuration

```eos
!
ip route vrf MGMT 0.0.0.0/0 10.30.0.1
```

### Router BGP

ASN Notation: asplain

#### Router BGP Summary

| BGP AS | Router ID |
| ------ | --------- |
| 65100 | 10.101.0.1 |

| BGP Tuning |
| ---------- |
| bgp bestpath d-path |
| no bgp default ipv4-unicast |
| maximum-paths 4 |

#### Router BGP Peer Groups

##### EVPN-OVERLAY-CORE

| Settings | Value |
| -------- | ----- |
| Address Family | evpn |
| Source | Loopback0 |
| BFD | True |
| Ebgp multihop | 15 |
| Send community | all |
| Maximum routes | 0 (no limit) |

##### EVPN-OVERLAY-PEERS

| Settings | Value |
| -------- | ----- |
| Address Family | evpn |
| Next-hop unchanged | True |
| Source | Loopback0 |
| BFD | True |
| Ebgp multihop | 3 |
| Send community | all |
| Maximum routes | 0 (no limit) |

##### IPv4-UNDERLAY-PEERS

| Settings | Value |
| -------- | ----- |
| Address Family | ipv4 |
| Send community | all |
| Maximum routes | 256000 |

#### BGP Neighbors

| Neighbor | Remote AS | VRF | Shutdown | Send-community | Maximum-routes | Maximum-accepted-routes | Maximum-advertised-routes | Allowas-in | BFD | RIB Pre-Policy Retain | Route-Reflector Client | Passive | TTL Max Hops |
| -------- | --------- | --- | -------- | -------------- | -------------- | ----------------------- | ------------------------- | ---------- | --- | --------------------- | ---------------------- | ------- | ------------ |
| 10.100.0.1 | 65200 | default | - | - | - | - | - | - | - | - | - | - | - |
| 10.100.0.3 | 65200 | default | - | - | - | - | - | - | - | - | - | - | - |
| 10.101.1.1 | 65101 | default | - | Inherited from peer group EVPN-OVERLAY-PEERS | Inherited from peer group EVPN-OVERLAY-PEERS | - | - | - | Inherited from peer group EVPN-OVERLAY-PEERS | - | - | - | - |
| 10.101.1.2 | 65101 | default | - | Inherited from peer group EVPN-OVERLAY-PEERS | Inherited from peer group EVPN-OVERLAY-PEERS | - | - | - | Inherited from peer group EVPN-OVERLAY-PEERS | - | - | - | - |
| 10.101.1.3 | 65102 | default | - | Inherited from peer group EVPN-OVERLAY-PEERS | Inherited from peer group EVPN-OVERLAY-PEERS | - | - | - | Inherited from peer group EVPN-OVERLAY-PEERS | - | - | - | - |
| 10.101.1.4 | 65102 | default | - | Inherited from peer group EVPN-OVERLAY-PEERS | Inherited from peer group EVPN-OVERLAY-PEERS | - | - | - | Inherited from peer group EVPN-OVERLAY-PEERS | - | - | - | - |
| 10.101.1.5 | 65103 | default | - | Inherited from peer group EVPN-OVERLAY-PEERS | Inherited from peer group EVPN-OVERLAY-PEERS | - | - | - | Inherited from peer group EVPN-OVERLAY-PEERS | - | - | - | - |
| 10.101.1.6 | 65103 | default | - | Inherited from peer group EVPN-OVERLAY-PEERS | Inherited from peer group EVPN-OVERLAY-PEERS | - | - | - | Inherited from peer group EVPN-OVERLAY-PEERS | - | - | - | - |
| 10.101.10.1 | 65101 | default | - | Inherited from peer group IPv4-UNDERLAY-PEERS | Inherited from peer group IPv4-UNDERLAY-PEERS | - | - | - | - | - | - | - | - |
| 10.101.10.5 | 65101 | default | - | Inherited from peer group IPv4-UNDERLAY-PEERS | Inherited from peer group IPv4-UNDERLAY-PEERS | - | - | - | - | - | - | - | - |
| 10.101.10.9 | 65102 | default | - | Inherited from peer group IPv4-UNDERLAY-PEERS | Inherited from peer group IPv4-UNDERLAY-PEERS | - | - | - | - | - | - | - | - |
| 10.101.10.13 | 65102 | default | - | Inherited from peer group IPv4-UNDERLAY-PEERS | Inherited from peer group IPv4-UNDERLAY-PEERS | - | - | - | - | - | - | - | - |
| 10.101.10.17 | 65103 | default | - | Inherited from peer group IPv4-UNDERLAY-PEERS | Inherited from peer group IPv4-UNDERLAY-PEERS | - | - | - | - | - | - | - | - |
| 10.101.10.21 | 65103 | default | - | Inherited from peer group IPv4-UNDERLAY-PEERS | Inherited from peer group IPv4-UNDERLAY-PEERS | - | - | - | - | - | - | - | - |
| 10.102.0.1 | 65200 | default | - | Inherited from peer group EVPN-OVERLAY-CORE | Inherited from peer group EVPN-OVERLAY-CORE | - | - | - | Inherited from peer group EVPN-OVERLAY-CORE | - | - | - | - |
| 10.102.0.2 | 65200 | default | - | Inherited from peer group EVPN-OVERLAY-CORE | Inherited from peer group EVPN-OVERLAY-CORE | - | - | - | Inherited from peer group EVPN-OVERLAY-CORE | - | - | - | - |

#### Router BGP EVPN Address Family

##### EVPN Peer Groups

| Peer Group | Activate | Route-map In | Route-map Out | Peer-tag In | Peer-tag Out | Encapsulation | Next-hop-self Source Interface |
| ---------- | -------- | ------------ | ------------- | ----------- | ------------ | ------------- | ------------------------------ |
| EVPN-OVERLAY-CORE | True | - | - | - | - | default | - |
| EVPN-OVERLAY-PEERS | True | - | - | - | - | default | - |

##### EVPN DCI Gateway Summary

| Settings | Value |
| -------- | ----- |
| Local Domain | 65100:1 |
| Remote Domain | 65200:2 |
| Remote Domain Peer Groups | EVPN-OVERLAY-CORE |
| L3 Gateway Configured | True |
| L3 Gateway Inter-domain | True |
| All Domain: Ethernet-Segment Identifier | 0000:0000:0001:0001:0001 |
| All Domain: Ethernet-Segment import Route-Target | 00:00:00:01:00:01 |

#### Router BGP VLANs

| VLAN | Route-Distinguisher | Both Route-Target | Import Route Target | Export Route-Target | Redistribute |
| ---- | ------------------- | ----------------- | ------------------- | ------------------- | ------------ |
| 110 | 10.101.0.1:110 | 110:110<br>remote 110:110 | - | - | learned |
| 210 | 10.101.0.1:210 | 210:210<br>remote 210:210 | - | - | learned |
| 310 | 10.101.0.1:310 | 310:310<br>remote 310:310 | - | - | learned |
| 399 | 10.101.0.1:399 | 399:399<br>remote 399:399 | - | - | learned |

#### Router BGP VRFs

| VRF | Route-Distinguisher | Redistribute | Graceful Restart |
| --- | ------------------- | ------------ | ---------------- |
| EXT | 10.101.0.1:10 | connected | - |
| PRIV | 10.101.0.1:30 | connected | - |
| WEW | 10.101.0.1:20 | connected | - |

#### Router BGP Device Configuration

```eos
!
router bgp 65100
   router-id 10.101.0.1
   no bgp default ipv4-unicast
   maximum-paths 4
   bgp bestpath d-path
   neighbor EVPN-OVERLAY-CORE peer group
   neighbor EVPN-OVERLAY-CORE update-source Loopback0
   neighbor EVPN-OVERLAY-CORE bfd
   neighbor EVPN-OVERLAY-CORE ebgp-multihop 15
   neighbor EVPN-OVERLAY-CORE send-community
   neighbor EVPN-OVERLAY-CORE maximum-routes 0
   neighbor EVPN-OVERLAY-PEERS peer group
   neighbor EVPN-OVERLAY-PEERS next-hop-unchanged
   neighbor EVPN-OVERLAY-PEERS update-source Loopback0
   neighbor EVPN-OVERLAY-PEERS bfd
   neighbor EVPN-OVERLAY-PEERS ebgp-multihop 3
   neighbor EVPN-OVERLAY-PEERS send-community
   neighbor EVPN-OVERLAY-PEERS maximum-routes 0
   neighbor IPv4-UNDERLAY-PEERS peer group
   neighbor IPv4-UNDERLAY-PEERS send-community
   neighbor IPv4-UNDERLAY-PEERS maximum-routes 256000
   neighbor 10.100.0.1 remote-as 65200
   neighbor 10.100.0.1 description DCI_marpla-dc-2-s01_Ethernet7
   neighbor 10.100.0.1 route-map RM-BGP-10.100.0.1-IN in
   neighbor 10.100.0.1 route-map RM-BGP-10.100.0.1-OUT out
   neighbor 10.100.0.3 remote-as 65200
   neighbor 10.100.0.3 description DCI_marpla-dc-2-s02_Ethernet8
   neighbor 10.100.0.3 route-map RM-BGP-10.100.0.3-IN in
   neighbor 10.100.0.3 route-map RM-BGP-10.100.0.3-OUT out
   neighbor 10.101.1.1 peer group EVPN-OVERLAY-PEERS
   neighbor 10.101.1.1 remote-as 65101
   neighbor 10.101.1.1 description marpla-dc-1-wew-l01_Loopback0
   neighbor 10.101.1.2 peer group EVPN-OVERLAY-PEERS
   neighbor 10.101.1.2 remote-as 65101
   neighbor 10.101.1.2 description marpla-dc-1-wew-l02_Loopback0
   neighbor 10.101.1.3 peer group EVPN-OVERLAY-PEERS
   neighbor 10.101.1.3 remote-as 65102
   neighbor 10.101.1.3 description marpla-dc-1-priv-l03_Loopback0
   neighbor 10.101.1.4 peer group EVPN-OVERLAY-PEERS
   neighbor 10.101.1.4 remote-as 65102
   neighbor 10.101.1.4 description marpla-dc-1-priv-l04_Loopback0
   neighbor 10.101.1.5 peer group EVPN-OVERLAY-PEERS
   neighbor 10.101.1.5 remote-as 65103
   neighbor 10.101.1.5 description marpla-dc-1-ext-l05_Loopback0
   neighbor 10.101.1.6 peer group EVPN-OVERLAY-PEERS
   neighbor 10.101.1.6 remote-as 65103
   neighbor 10.101.1.6 description marpla-dc-1-ext-l06_Loopback0
   neighbor 10.101.10.1 peer group IPv4-UNDERLAY-PEERS
   neighbor 10.101.10.1 remote-as 65101
   neighbor 10.101.10.1 description marpla-dc-1-wew-l01_Ethernet1
   neighbor 10.101.10.5 peer group IPv4-UNDERLAY-PEERS
   neighbor 10.101.10.5 remote-as 65101
   neighbor 10.101.10.5 description marpla-dc-1-wew-l02_Ethernet1
   neighbor 10.101.10.9 peer group IPv4-UNDERLAY-PEERS
   neighbor 10.101.10.9 remote-as 65102
   neighbor 10.101.10.9 description marpla-dc-1-priv-l03_Ethernet1
   neighbor 10.101.10.13 peer group IPv4-UNDERLAY-PEERS
   neighbor 10.101.10.13 remote-as 65102
   neighbor 10.101.10.13 description marpla-dc-1-priv-l04_Ethernet1
   neighbor 10.101.10.17 peer group IPv4-UNDERLAY-PEERS
   neighbor 10.101.10.17 remote-as 65103
   neighbor 10.101.10.17 description marpla-dc-1-ext-l05_Ethernet1
   neighbor 10.101.10.21 peer group IPv4-UNDERLAY-PEERS
   neighbor 10.101.10.21 remote-as 65103
   neighbor 10.101.10.21 description marpla-dc-1-ext-l06_Ethernet1
   neighbor 10.102.0.1 peer group EVPN-OVERLAY-CORE
   neighbor 10.102.0.1 remote-as 65200
   neighbor 10.102.0.1 description marpla-dc-2-s01
   neighbor 10.102.0.2 peer group EVPN-OVERLAY-CORE
   neighbor 10.102.0.2 remote-as 65200
   neighbor 10.102.0.2 description marpla-dc-2-s02
   redistribute connected route-map RM-CONN-2-BGP
   !
   vlan 110
      rd 10.101.0.1:110
      rd evpn domain remote 10.101.0.1:110
      route-target both 110:110
      route-target import export evpn domain remote 110:110
      redistribute learned
   !
   vlan 210
      rd 10.101.0.1:210
      rd evpn domain remote 10.101.0.1:210
      route-target both 210:210
      route-target import export evpn domain remote 210:210
      redistribute learned
   !
   vlan 310
      rd 10.101.0.1:310
      rd evpn domain remote 10.101.0.1:310
      route-target both 310:310
      route-target import export evpn domain remote 310:310
      redistribute learned
   !
   vlan 399
      rd 10.101.0.1:399
      rd evpn domain remote 10.101.0.1:399
      route-target both 399:399
      route-target import export evpn domain remote 399:399
      redistribute learned
   !
   address-family evpn
      neighbor EVPN-OVERLAY-CORE activate
      neighbor EVPN-OVERLAY-CORE domain remote
      neighbor EVPN-OVERLAY-PEERS activate
      domain identifier 65100:1
      domain identifier 65200:2 remote
      neighbor default next-hop-self received-evpn-routes route-type ip-prefix inter-domain
      !
      evpn ethernet-segment domain all
         identifier 0000:0000:0001:0001:0001
         route-target import 00:00:00:01:00:01
   !
   address-family ipv4
      no neighbor EVPN-OVERLAY-CORE activate
      no neighbor EVPN-OVERLAY-PEERS activate
      neighbor IPv4-UNDERLAY-PEERS activate
      neighbor 10.100.0.1 activate
      neighbor 10.100.0.3 activate
   !
   vrf EXT
      rd 10.101.0.1:10
      route-target import evpn 10:10
      route-target export evpn 10:10
      router-id 10.101.0.1
      redistribute connected
   !
   vrf PRIV
      rd 10.101.0.1:30
      route-target import evpn 30:30
      route-target export evpn 30:30
      router-id 10.101.0.1
      redistribute connected
   !
   vrf WEW
      rd 10.101.0.1:20
      route-target import evpn 20:20
      route-target export evpn 20:20
      router-id 10.101.0.1
      redistribute connected
```

## BFD

### Router BFD

#### Router BFD Multihop Summary

| Interval | Minimum RX | Multiplier |
| -------- | ---------- | ---------- |
| 300 | 300 | 3 |

#### Router BFD Device Configuration

```eos
!
router bfd
   multihop interval 300 min-rx 300 multiplier 3
```

## Multicast

### IP IGMP Snooping

#### IP IGMP Snooping Summary

| IGMP Snooping | Fast Leave | Interface Restart Query | Proxy | Restart Query Interval | Robustness Variable |
| ------------- | ---------- | ----------------------- | ----- | ---------------------- | ------------------- |
| Enabled | - | - | - | - | - |

#### IP IGMP Snooping Device Configuration

```eos
```

## Filters

### Prefix-lists

#### Prefix-lists Summary

##### PL-DCI-IN

| Sequence | Action |
| -------- | ------ |
| 10 | permit 10.102.0.0/24 eq 32 |
| 20 | permit 10.102.3.0/24 eq 32 |

##### PL-DCI-OUT

| Sequence | Action |
| -------- | ------ |
| 10 | permit 10.101.0.0/24 eq 32 |
| 20 | permit 10.101.3.0/24 eq 32 |

##### PL-LOOPBACKS-EVPN-OVERLAY

| Sequence | Action |
| -------- | ------ |
| 10 | permit 10.101.0.0/24 eq 32 |
| 20 | permit 10.101.3.0/24 eq 32 |

#### Prefix-lists Device Configuration

```eos
!
ip prefix-list PL-DCI-IN
   seq 10 permit 10.102.0.0/24 eq 32
   seq 20 permit 10.102.3.0/24 eq 32
!
ip prefix-list PL-DCI-OUT
   seq 10 permit 10.101.0.0/24 eq 32
   seq 20 permit 10.101.3.0/24 eq 32
!
ip prefix-list PL-LOOPBACKS-EVPN-OVERLAY
   seq 10 permit 10.101.0.0/24 eq 32
   seq 20 permit 10.101.3.0/24 eq 32
```

### Route-maps

#### Route-maps Summary

##### RM-BGP-10.100.0.1-IN

| Sequence | Type | Match | Set | Sub-Route-Map | Continue |
| -------- | ---- | ----- | --- | ------------- | -------- |
| 10 | permit | ip address prefix-list PL-DCI-IN | - | - | - |

##### RM-BGP-10.100.0.1-OUT

| Sequence | Type | Match | Set | Sub-Route-Map | Continue |
| -------- | ---- | ----- | --- | ------------- | -------- |
| 10 | permit | ip address prefix-list PL-DCI-OUT | - | - | - |
| 20 | deny | - | - | - | - |

##### RM-BGP-10.100.0.3-IN

| Sequence | Type | Match | Set | Sub-Route-Map | Continue |
| -------- | ---- | ----- | --- | ------------- | -------- |
| 10 | permit | ip address prefix-list PL-DCI-IN | - | - | - |

##### RM-BGP-10.100.0.3-OUT

| Sequence | Type | Match | Set | Sub-Route-Map | Continue |
| -------- | ---- | ----- | --- | ------------- | -------- |
| 10 | permit | ip address prefix-list PL-DCI-OUT | - | - | - |
| 20 | deny | - | - | - | - |

##### RM-CONN-2-BGP

| Sequence | Type | Match | Set | Sub-Route-Map | Continue |
| -------- | ---- | ----- | --- | ------------- | -------- |
| 10 | permit | ip address prefix-list PL-LOOPBACKS-EVPN-OVERLAY | - | - | - |

#### Route-maps Device Configuration

```eos
!
route-map RM-BGP-10.100.0.1-IN permit 10
   match ip address prefix-list PL-DCI-IN
!
route-map RM-BGP-10.100.0.1-OUT permit 10
   match ip address prefix-list PL-DCI-OUT
!
route-map RM-BGP-10.100.0.1-OUT deny 20
!
route-map RM-BGP-10.100.0.3-IN permit 10
   match ip address prefix-list PL-DCI-IN
!
route-map RM-BGP-10.100.0.3-OUT permit 10
   match ip address prefix-list PL-DCI-OUT
!
route-map RM-BGP-10.100.0.3-OUT deny 20
!
route-map RM-CONN-2-BGP permit 10
   match ip address prefix-list PL-LOOPBACKS-EVPN-OVERLAY
```

## VRF Instances

### VRF Instances Summary

| VRF Name | IP Routing |
| -------- | ---------- |
| EXT | enabled |
| MGMT | disabled |
| PRIV | enabled |
| WEW | enabled |

### VRF Instances Device Configuration

```eos
!
vrf instance EXT
!
vrf instance MGMT
!
vrf instance PRIV
!
vrf instance WEW
```
