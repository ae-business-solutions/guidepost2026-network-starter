# Overview
Build a throwaway Azure Virtual WAN lab to learn how hub routing works, then tear it down.

# Tools
- Terraform with the `azurerm` provider
- Azure CLI login already done; use the subscription I name

# Topology
- One Virtual WAN with two hubs: East US 2 and West Europe
- Three spoke VNets: two in East US 2, one in West Europe, each connected to its local hub
- One small Linux VM per spoke for ping and traceroute tests, reachable through Azure Bastion or serial console only (no public IPs)

# Output
- A Terraform project with variables for subscription, regions and a name prefix
- Every resource tagged `purpose=lab` and `owner=<me>`
- Outputs: VM private IPs and the commands to test spoke-to-spoke reachability
- A README with apply, test and `terraform destroy`, and a rough hourly cost

# Architecture
- Smallest sizes that work
- Nothing reachable from the internet
- Tell me before anything with a large hourly cost (VPN or ExpressRoute gateways, firewalls)

AWS version: swap the topology for one Transit Gateway in us-east-2, three VPCs attached, one route table per environment.
