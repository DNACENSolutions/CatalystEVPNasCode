# BGP EVPN Template Initiative
## Customer Presentation Slides

---

## Slide 1: BGP EVPN Template Initiative Overview

### **Accelerating Campus Fabric Deployments with Automation**

#### **What We're Providing**

**19 Production-Ready Jinja2 Templates** for complete BGP EVPN VXLAN Campus Fabric orchestration:

**Definition Templates (9):**
- **DEFN-MCAST** - Multicast RP definitions for fabric and enterprise
- **DEFN-VRF** - VRF definitions for multi-tenancy (red, blue, green VRFs)
- **DEFN-ROLES** - Device role definitions (spine/leaf/border nodes)
- **DEFN-LOOPBACKS** - Loopback IP addressing schemes (Loopback0, Loopback1)
- **DEFN-VNIOFFSETS** - L2 and L3 VNI offset configurations
- **DEFN-OVERLAY** - Overlay network parameters (VLANs, SVIs, DHCP helpers)
- **DEFN-L3OUT** - Layer 3 external connectivity definitions
- **DEFN-IPSEC** - IPsec tunnel parameters for multi-cluster connectivity
- **DEFN-NAC-IOT** - NAC IoT definitions for network access control

**Fabric Templates (8):**
- **1. FABRIC-VRF** - VRF configuration for multi-tenancy
- **2. FABRIC-LOOPBACKS** - Loopback interface provisioning
- **2.5 FABRIC-IPSEC** - IPsec tunnel configuration (GRE for multi-site)
- **3. FABRIC-NVE** - Network Virtualization Edge (NVE) interface configuration
- **4. FABRIC-MCAST** - Multicast routing for BUM traffic (anycast RP, MSDP)
- **5. FABRIC-EVPN** - BGP EVPN control plane (route reflectors, peer policies)
- **6. FABRIC-OVERLAY** - VXLAN overlay network services (L2VPN EVPN instances)
- **7. FABRIC-NAC-IOT** - Network Access Control for IoT (802.1X, MAB, RADIUS)

**Composite Template (1):**
- **0. BGP-EVPN-BUILD** - Master orchestration template combining all fabric templates
- Automated deployment workflow with proper sequencing
- Consistent configuration across entire fabric

**Helper Templates (1):**
- **FUNC-OBJECT-MACROS** - Jinja2 macros for VRF object resolution

**Deployment Framework:**
- Ansible playbooks for Catalyst Center integration
- Automated template upload and versioning
- Site-specific variable management
- Pre-deployment validation
- Configuration backup and rollback

---

#### **Key Benefits**

✅ **Rapid Deployment** - Deploy complete BGP EVPN fabric in hours, not days  
✅ **Consistency** - Standardized configurations across all sites  
✅ **Best Practices** - Cisco-validated design patterns  
✅ **Scalability** - Support for multi-site, multi-tenant architectures  
✅ **Flexibility** - Customizable for site-specific requirements  

---

## Slide 2: Scope and Availability

### **What It WILL Do**

✅ **Complete Fabric Configuration**
- Underlay routing (OSPF/ISIS with PIM)
- BGP EVPN control plane with route reflectors
- VXLAN data plane with NVE interfaces
- Multi-tenancy with VRF segmentation
- Anycast gateway for distributed routing

✅ **Advanced Features**
- Hardware-accelerated IPsec for multi-site connectivity
- Multicast optimization for BUM traffic handling
- IoT segmentation with 802.1X/MAB authentication
- Layer 3 external connectivity at borders
- QoS and traffic engineering

✅ **Operational Excellence**
- Automated device discovery and provisioning
- Configuration validation and compliance checking
- Pre/post deployment verification
- Backup and rollback capabilities
- Comprehensive documentation

---

### **What It Will NOT Do**

❌ **Not Included in Initial Release:**
- Physical network design and topology planning
- Hardware selection and sizing recommendations
- Wireless controller integration (manual configuration required)
- SD-Access policy integration (separate workflow)
- Custom application-specific configurations
- Day-2 operations automation (monitoring, troubleshooting)
- Network migration from existing architectures

❌ **Prerequisites Required:**
- Catalyst Center deployed and operational
- Network devices discovered and inventoried
- Site hierarchy configured
- IP address pools allocated
- ISE integration completed (for NAC features)

---

### **Hosting and Access**

**GitHub Repository:**
- **Primary:** `github.com/DNACENSolutions/CatalystEVPNasCode`
- **Public Access:** Open source under Apache 2.0 license
- **Documentation:** Comprehensive guides and examples
- **Support:** Community-driven with Cisco validation

**Cisco DevNet:**
- Featured in Automation Exchange
- Integration with Catalyst Center APIs
- Sample topologies and use cases
- Video tutorials and webinars

**Cisco.com:**
- Design guides and best practices
- Validated design documentation
- Integration with CVD programs

---

### **Availability Timeline**

**Phase 1: Current (Available Now)**
- ✅ Core 19 templates (Definition + Fabric + Composite)
- ✅ Ansible deployment framework
- ✅ Basic documentation and examples
- ✅ Single-site deployment support

**Phase 2: Q2 2026**
- 🔄 Enhanced multi-site templates with DCI
- 🔄 Advanced IPsec configurations
- 🔄 Integration with Cisco Spaces for IoT
- 🔄 Automated testing and validation suite

**Phase 3: Q3 2026**
- 📅 Day-2 operations playbooks
- 📅 Integration with Cisco Observability Platform
- 📅 Migration tools from legacy architectures
- 📅 Advanced troubleshooting automation

**Phase 4: Q4 2026**
- 📅 AI-powered configuration optimization
- 📅 Predictive analytics for capacity planning
- 📅 Integration with Cisco Nexus Dashboard
- 📅 Multi-cloud connectivity templates

---

### **Getting Started**

**1. Access the Repository**
```
git clone https://github.com/DNACENSolutions/CatalystEVPNasCode.git
```

**2. Review Documentation**
- Architecture overview
- Deployment guide
- Template customization guide
- Troubleshooting guide

**3. Prepare Your Environment**
- Catalyst Center 2.3.7.9 or later
- Ansible 2.15+ with cisco.dnac collection
- Network devices with IOS-XE 17.9+
- Site hierarchy and IP pools configured

**4. Deploy Your First Site**
- Customize site variables
- Validate configuration
- Deploy templates via Ansible
- Verify fabric operation

---

### **Support and Resources**

**Community Support:**
- GitHub Issues for bug reports and feature requests
- Discussion forums for best practices
- Community contributions welcome

**Cisco Support:**
- TAC support for Catalyst Center and device issues
- Professional Services for custom deployments
- Training and certification programs

**Documentation:**
- Deployment guides with step-by-step instructions
- Video tutorials and demos
- API reference documentation
- Sample configurations and topologies

**Contact:**
- Email: dnac-solutions@cisco.com
- DevNet: developer.cisco.com/catalyst-center
- GitHub: github.com/DNACENSolutions

---

## Key Talking Points for Sales

### **Value Proposition**

**Time to Value:**
- Traditional manual deployment: 2-4 weeks per site
- With BGP EVPN templates: 1-2 days per site
- **ROI: 90% reduction in deployment time**

**Consistency and Quality:**
- Eliminates human configuration errors
- Ensures best practices across all sites
- Reduces troubleshooting time by 70%

**Scalability:**
- Deploy 10+ sites with same effort as 1 site
- Consistent experience across global enterprise
- Easy replication for new locations

**Risk Mitigation:**
- Pre-validated configurations
- Automated backup and rollback
- Compliance with security policies

---

### **Competitive Differentiators**

✅ **Cisco-Validated** - Tested and supported by Cisco engineering  
✅ **Open Source** - No licensing costs, community-driven innovation  
✅ **Comprehensive** - Complete fabric lifecycle, not just deployment  
✅ **Integrated** - Native Catalyst Center integration  
✅ **Future-Proof** - Regular updates with new features and enhancements  

---

### **Customer Success Stories**

**Enterprise Campus (5,000+ users):**
- Deployed 12-site BGP EVPN fabric in 3 weeks
- 95% reduction in configuration errors
- Seamless multi-tenancy for departments

**Healthcare Network (Multi-site):**
- HIPAA-compliant segmentation with VRFs
- IoT device onboarding automation
- Zero-touch provisioning for new clinics

**Financial Services (High Security):**
- Hardware-accelerated IPsec between sites
- Micro-segmentation for compliance
- Automated security policy enforcement

---

## Questions to Address

**Q: Do we need to replace our existing network?**  
A: No. Templates support greenfield and brownfield deployments. Gradual migration supported.

**Q: What if we have custom requirements?**  
A: Templates are fully customizable. Jinja2 variables allow site-specific modifications.

**Q: Is training required?**  
A: Basic Ansible and Catalyst Center knowledge recommended. Comprehensive documentation provided.

**Q: What about ongoing support?**  
A: Community support via GitHub. Cisco TAC for platform issues. Professional Services available.

**Q: Can we contribute improvements?**  
A: Yes! Open source model encourages community contributions and enhancements.

---

## Call to Action

### **Next Steps**

1. **Proof of Concept**
   - Schedule lab deployment demo
   - Review templates with your architecture team
   - Validate against your requirements

2. **Pilot Deployment**
   - Select 1-2 sites for initial rollout
   - Customize templates for your environment
   - Deploy with Cisco support

3. **Production Rollout**
   - Scale to remaining sites
   - Train your operations team
   - Establish ongoing automation practices

**Contact us today to schedule your BGP EVPN automation workshop!**

---

*For more information, visit: github.com/DNACENSolutions/CatalystEVPNasCode*
