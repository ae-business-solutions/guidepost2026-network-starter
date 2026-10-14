# Overview
Build a Containerlab lab for practicing network automation: a small leaf-spine fabric that works on first boot.

# Tools
- Containerlab
- Arista cEOS for the switches (image already imported as `ceos:4.34.2F`)
- Alpine Linux containers for hosts

# Topology
- 2 spines and 4 leafs; leafs in two MLAG pairs
- eBGP underlay, one ASN per leaf pair
- EVPN/VXLAN overlay with one tenant VRF and VLANs 10 and 20
- One Linux host per leaf pair, in VLAN 10, with an IP and default gateway

# Output
- `fabric.clab.yml` plus one startup config per switch
- Fixed management IPs, and eAPI enabled on every switch
- A read-only user `collector` (role `network-operator`) on every switch
- A short README: deploy, check BGP and ping between hosts, destroy

# Architecture
- Everything works on first boot with no manual steps
- No external network access needed after the images are pulled
