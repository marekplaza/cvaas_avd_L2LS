# AVD_FABRIC

## Table of Contents

- [Fabric Switches and Management IP](#fabric-switches-and-management-ip)
  - [Fabric Switches with inband Management IP](#fabric-switches-with-inband-management-ip)
- [Fabric Topology](#fabric-topology)
- [Fabric IP Allocation](#fabric-ip-allocation)
  - [Fabric Point-To-Point Links](#fabric-point-to-point-links)
  - [Point-To-Point Links Node Allocation](#point-to-point-links-node-allocation)
  - [Loopback Interfaces (BGP EVPN Peering)](#loopback-interfaces-bgp-evpn-peering)
  - [Loopback0 Interfaces Node Allocation](#loopback0-interfaces-node-allocation)
  - [VTEP Loopback VXLAN Tunnel Source Interfaces (VTEPs Only)](#vtep-loopback-vxlan-tunnel-source-interfaces-vteps-only)
  - [VTEP Loopback Node allocation](#vtep-loopback-node-allocation)

## Fabric Switches and Management IP

| POD | Type | Node | Management IP | Platform | Provisioned in CloudVision | Serial Number |
| --- | ---- | ---- | ------------- | -------- | -------------------------- | ------------- |
| marpla-POD1 | l3leaf | marpla-l01 | 10.0.2.1/16 | cEOS | Provisioned | - |
| marpla-POD1 | l3leaf | marpla-l02 | 10.0.2.2/16 | cEOS | Provisioned | - |
| marpla-POD1 | l3leaf | marpla-l03 | 10.0.2.3/16 | cEOS | Provisioned | - |
| marpla-POD1 | l3leaf | marpla-l04 | 10.0.2.4/16 | cEOS | Provisioned | - |
| marpla-POD1 | spine | marpla-s01 | 10.0.1.1/16 | cEOS | Provisioned | - |
| marpla-POD1 | spine | marpla-s02 | 10.0.1.2/16 | cEOS | Provisioned | - |

> Provision status is based on Ansible inventory declaration and do not represent real status from CloudVision.

### Fabric Switches with inband Management IP

| POD | Type | Node | Management IP | Inband Interface |
| --- | ---- | ---- | ------------- | ---------------- |

## Fabric Topology

| Type | Node | Node Interface | Peer Type | Peer Node | Peer Interface |
| ---- | ---- | -------------- | --------- | --------- | -------------- |
| l3leaf | marpla-l01 | Ethernet1 | spine | marpla-s01 | Ethernet1 |
| l3leaf | marpla-l01 | Ethernet2 | spine | marpla-s02 | Ethernet1 |
| l3leaf | marpla-l01 | Ethernet3 | mlag_peer | marpla-l02 | Ethernet3 |
| l3leaf | marpla-l01 | Ethernet4 | mlag_peer | marpla-l02 | Ethernet4 |
| l3leaf | marpla-l02 | Ethernet1 | spine | marpla-s01 | Ethernet2 |
| l3leaf | marpla-l02 | Ethernet2 | spine | marpla-s02 | Ethernet2 |
| l3leaf | marpla-l03 | Ethernet1 | spine | marpla-s01 | Ethernet3 |
| l3leaf | marpla-l03 | Ethernet2 | spine | marpla-s02 | Ethernet3 |
| l3leaf | marpla-l03 | Ethernet3 | mlag_peer | marpla-l04 | Ethernet3 |
| l3leaf | marpla-l03 | Ethernet4 | mlag_peer | marpla-l04 | Ethernet4 |
| l3leaf | marpla-l04 | Ethernet1 | spine | marpla-s01 | Ethernet4 |
| l3leaf | marpla-l04 | Ethernet2 | spine | marpla-s02 | Ethernet4 |

## Fabric IP Allocation

### Fabric Point-To-Point Links

| Uplink IPv4 Pool | Available Addresses | Assigned addresses | Assigned Address % |
| ---------------- | ------------------- | ------------------ | ------------------ |
| 100.65.0.0/24 | 256 | 16 | 6.25 % |

### Point-To-Point Links Node Allocation

| Node | Node Interface | Node IP Address | Peer Node | Peer Interface | Peer IP Address |
| ---- | -------------- | --------------- | --------- | -------------- | --------------- |
| marpla-l01 | Ethernet1 | 100.65.0.1/31 | marpla-s01 | Ethernet1 | 100.65.0.0/31 |
| marpla-l01 | Ethernet2 | 100.65.0.3/31 | marpla-s02 | Ethernet1 | 100.65.0.2/31 |
| marpla-l02 | Ethernet1 | 100.65.0.5/31 | marpla-s01 | Ethernet2 | 100.65.0.4/31 |
| marpla-l02 | Ethernet2 | 100.65.0.7/31 | marpla-s02 | Ethernet2 | 100.65.0.6/31 |
| marpla-l03 | Ethernet1 | 100.65.0.9/31 | marpla-s01 | Ethernet3 | 100.65.0.8/31 |
| marpla-l03 | Ethernet2 | 100.65.0.11/31 | marpla-s02 | Ethernet3 | 100.65.0.10/31 |
| marpla-l04 | Ethernet1 | 100.65.0.13/31 | marpla-s01 | Ethernet4 | 100.65.0.12/31 |
| marpla-l04 | Ethernet2 | 100.65.0.15/31 | marpla-s02 | Ethernet4 | 100.65.0.14/31 |

### Loopback Interfaces (BGP EVPN Peering)

| Loopback Pool | Available Addresses | Assigned addresses | Assigned Address % |
| ------------- | ------------------- | ------------------ | ------------------ |
| 100.64.255.0/24 | 256 | 2 | 0.79 % |
| 100.65.255.0/24 | 256 | 4 | 1.57 % |

### Loopback0 Interfaces Node Allocation

| POD | Node | Loopback0 |
| --- | ---- | --------- |
| marpla-POD1 | marpla-l01 | 100.65.255.3/32 |
| marpla-POD1 | marpla-l02 | 100.65.255.4/32 |
| marpla-POD1 | marpla-l03 | 100.65.255.5/32 |
| marpla-POD1 | marpla-l04 | 100.65.255.6/32 |
| marpla-POD1 | marpla-s01 | 100.64.255.1/32 |
| marpla-POD1 | marpla-s02 | 100.64.255.2/32 |

### VTEP Loopback VXLAN Tunnel Source Interfaces (VTEPs Only)

| VTEP Loopback Pool | Available Addresses | Assigned addresses | Assigned Address % |
| ------------------ | ------------------- | ------------------ | ------------------ |
| 100.65.254.0/24 | 256 | 4 | 1.57 % |

### VTEP Loopback Node allocation

| POD | Node | Loopback1 |
| --- | ---- | --------- |
| marpla-POD1 | marpla-l01 | 100.65.254.3/32 |
| marpla-POD1 | marpla-l02 | 100.65.254.3/32 |
| marpla-POD1 | marpla-l03 | 100.65.254.5/32 |
| marpla-POD1 | marpla-l04 | 100.65.254.5/32 |
