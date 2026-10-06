# MARPLA_DC1

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
| marpla-DC1-POD1 | l3leaf | marpla-dc-1-ext-l05 | 10.30.12.5/16 | cEOS | Provisioned | - |
| marpla-DC1-POD1 | l3leaf | marpla-dc-1-ext-l06 | 10.30.12.6/16 | cEOS | Provisioned | - |
| marpla-DC1-POD1 | l3leaf | marpla-dc-1-priv-l03 | 10.30.12.3/16 | cEOS | Provisioned | - |
| marpla-DC1-POD1 | l3leaf | marpla-dc-1-priv-l04 | 10.30.12.4/16 | cEOS | Provisioned | - |
| marpla-DC1-POD1 | spine | marpla-dc-1-s01 | 10.30.11.1/16 | cEOS | Provisioned | - |
| marpla-DC1-POD1 | spine | marpla-dc-1-s02 | 10.30.11.2/16 | cEOS | Provisioned | - |
| marpla-DC1-POD1 | l3leaf | marpla-dc-1-wew-l01 | 10.30.12.1/16 | cEOS | Provisioned | - |
| marpla-DC1-POD1 | l3leaf | marpla-dc-1-wew-l02 | 10.30.12.2/16 | cEOS | Provisioned | - |

> Provision status is based on Ansible inventory declaration and do not represent real status from CloudVision.

### Fabric Switches with inband Management IP

| POD | Type | Node | Management IP | Inband Interface |
| --- | ---- | ---- | ------------- | ---------------- |

## Fabric Topology

| Type | Node | Node Interface | Peer Type | Peer Node | Peer Interface |
| ---- | ---- | -------------- | --------- | --------- | -------------- |
| l3leaf | marpla-dc-1-ext-l05 | Ethernet1 | spine | marpla-dc-1-s01 | Ethernet5 |
| l3leaf | marpla-dc-1-ext-l05 | Ethernet2 | spine | marpla-dc-1-s02 | Ethernet5 |
| l3leaf | marpla-dc-1-ext-l05 | Ethernet3 | mlag_peer | marpla-dc-1-ext-l06 | Ethernet3 |
| l3leaf | marpla-dc-1-ext-l05 | Ethernet4 | mlag_peer | marpla-dc-1-ext-l06 | Ethernet4 |
| l3leaf | marpla-dc-1-ext-l06 | Ethernet1 | spine | marpla-dc-1-s01 | Ethernet6 |
| l3leaf | marpla-dc-1-ext-l06 | Ethernet2 | spine | marpla-dc-1-s02 | Ethernet6 |
| l3leaf | marpla-dc-1-priv-l03 | Ethernet1 | spine | marpla-dc-1-s01 | Ethernet3 |
| l3leaf | marpla-dc-1-priv-l03 | Ethernet2 | spine | marpla-dc-1-s02 | Ethernet3 |
| l3leaf | marpla-dc-1-priv-l03 | Ethernet3 | mlag_peer | marpla-dc-1-priv-l04 | Ethernet3 |
| l3leaf | marpla-dc-1-priv-l03 | Ethernet4 | mlag_peer | marpla-dc-1-priv-l04 | Ethernet4 |
| l3leaf | marpla-dc-1-priv-l04 | Ethernet1 | spine | marpla-dc-1-s01 | Ethernet4 |
| l3leaf | marpla-dc-1-priv-l04 | Ethernet2 | spine | marpla-dc-1-s02 | Ethernet4 |
| spine | marpla-dc-1-s01 | Ethernet1 | l3leaf | marpla-dc-1-wew-l01 | Ethernet1 |
| spine | marpla-dc-1-s01 | Ethernet2 | l3leaf | marpla-dc-1-wew-l02 | Ethernet1 |
| spine | marpla-dc-1-s02 | Ethernet1 | l3leaf | marpla-dc-1-wew-l01 | Ethernet2 |
| spine | marpla-dc-1-s02 | Ethernet2 | l3leaf | marpla-dc-1-wew-l02 | Ethernet2 |
| l3leaf | marpla-dc-1-wew-l01 | Ethernet3 | mlag_peer | marpla-dc-1-wew-l02 | Ethernet3 |
| l3leaf | marpla-dc-1-wew-l01 | Ethernet4 | mlag_peer | marpla-dc-1-wew-l02 | Ethernet4 |

## Fabric IP Allocation

### Fabric Point-To-Point Links

| Uplink IPv4 Pool | Available Addresses | Assigned addresses | Assigned Address % |
| ---------------- | ------------------- | ------------------ | ------------------ |
| 10.101.10.0/24 | 256 | 24 | 9.38 % |

### Point-To-Point Links Node Allocation

| Node | Node Interface | Node IP Address | Peer Node | Peer Interface | Peer IP Address |
| ---- | -------------- | --------------- | --------- | -------------- | --------------- |
| marpla-dc-1-ext-l05 | Ethernet1 | 10.101.10.17/31 | marpla-dc-1-s01 | Ethernet5 | 10.101.10.16/31 |
| marpla-dc-1-ext-l05 | Ethernet2 | 10.101.10.19/31 | marpla-dc-1-s02 | Ethernet5 | 10.101.10.18/31 |
| marpla-dc-1-ext-l06 | Ethernet1 | 10.101.10.21/31 | marpla-dc-1-s01 | Ethernet6 | 10.101.10.20/31 |
| marpla-dc-1-ext-l06 | Ethernet2 | 10.101.10.23/31 | marpla-dc-1-s02 | Ethernet6 | 10.101.10.22/31 |
| marpla-dc-1-priv-l03 | Ethernet1 | 10.101.10.9/31 | marpla-dc-1-s01 | Ethernet3 | 10.101.10.8/31 |
| marpla-dc-1-priv-l03 | Ethernet2 | 10.101.10.11/31 | marpla-dc-1-s02 | Ethernet3 | 10.101.10.10/31 |
| marpla-dc-1-priv-l04 | Ethernet1 | 10.101.10.13/31 | marpla-dc-1-s01 | Ethernet4 | 10.101.10.12/31 |
| marpla-dc-1-priv-l04 | Ethernet2 | 10.101.10.15/31 | marpla-dc-1-s02 | Ethernet4 | 10.101.10.14/31 |
| marpla-dc-1-s01 | Ethernet1 | 10.101.10.0/31 | marpla-dc-1-wew-l01 | Ethernet1 | 10.101.10.1/31 |
| marpla-dc-1-s01 | Ethernet2 | 10.101.10.4/31 | marpla-dc-1-wew-l02 | Ethernet1 | 10.101.10.5/31 |
| marpla-dc-1-s02 | Ethernet1 | 10.101.10.2/31 | marpla-dc-1-wew-l01 | Ethernet2 | 10.101.10.3/31 |
| marpla-dc-1-s02 | Ethernet2 | 10.101.10.6/31 | marpla-dc-1-wew-l02 | Ethernet2 | 10.101.10.7/31 |

### Loopback Interfaces (BGP EVPN Peering)

| Loopback Pool | Available Addresses | Assigned addresses | Assigned Address % |
| ------------- | ------------------- | ------------------ | ------------------ |
| 10.101.0.0/24 | 256 | 2 | 0.79 % |
| 10.101.1.0/24 | 256 | 6 | 2.35 % |

### Loopback0 Interfaces Node Allocation

| POD | Node | Loopback0 |
| --- | ---- | --------- |
| marpla-DC1-POD1 | marpla-dc-1-ext-l05 | 10.101.1.5/32 |
| marpla-DC1-POD1 | marpla-dc-1-ext-l06 | 10.101.1.6/32 |
| marpla-DC1-POD1 | marpla-dc-1-priv-l03 | 10.101.1.3/32 |
| marpla-DC1-POD1 | marpla-dc-1-priv-l04 | 10.101.1.4/32 |
| marpla-DC1-POD1 | marpla-dc-1-s01 | 10.101.0.1/32 |
| marpla-DC1-POD1 | marpla-dc-1-s02 | 10.101.0.2/32 |
| marpla-DC1-POD1 | marpla-dc-1-wew-l01 | 10.101.1.1/32 |
| marpla-DC1-POD1 | marpla-dc-1-wew-l02 | 10.101.1.2/32 |

### VTEP Loopback VXLAN Tunnel Source Interfaces (VTEPs Only)

| VTEP Loopback Pool | Available Addresses | Assigned addresses | Assigned Address % |
| ------------------ | ------------------- | ------------------ | ------------------ |
| 10.101.2.0/24 | 256 | 6 | 2.35 % |

### VTEP Loopback Node allocation

| POD | Node | Loopback1 |
| --- | ---- | --------- |
| marpla-DC1-POD1 | marpla-dc-1-ext-l05 | 10.101.2.5/32 |
| marpla-DC1-POD1 | marpla-dc-1-ext-l06 | 10.101.2.5/32 |
| marpla-DC1-POD1 | marpla-dc-1-priv-l03 | 10.101.2.3/32 |
| marpla-DC1-POD1 | marpla-dc-1-priv-l04 | 10.101.2.3/32 |
| marpla-DC1-POD1 | marpla-dc-1-wew-l01 | 10.101.2.1/32 |
| marpla-DC1-POD1 | marpla-dc-1-wew-l02 | 10.101.2.1/32 |
