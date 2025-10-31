"""
Firewall Service - Multi-backend firewall management
"""
import logging
import subprocess
import shutil
from typing import List, Optional
from enum import Enum

from app.core.config import settings

logger = logging.getLogger(__name__)


class FirewallBackend(Enum):
    """Supported firewall backends"""
    NFTABLES = "nftables"
    IPTABLES = "iptables"
    UFW = "ufw"
    FIREWALLD = "firewalld"
    NONE = "none"


class FirewallService:
    """Manages firewall rules for Tor proxy pool"""
    
    def __init__(self):
        self.backend = self._detect_backend()
        logger.info(f"Using firewall backend: {self.backend.value}")
    
    def _detect_backend(self) -> FirewallBackend:
        """Auto-detect available firewall backend"""
        if settings.FIREWALL_BACKEND != "auto":
            try:
                return FirewallBackend(settings.FIREWALL_BACKEND)
            except ValueError:
                logger.warning(f"Invalid firewall backend: {settings.FIREWALL_BACKEND}, auto-detecting")
        
        # Check for available backends
        if shutil.which("firewall-cmd"):
            return FirewallBackend.FIREWALLD
        elif shutil.which("ufw"):
            return FirewallBackend.UFW
        elif shutil.which("nft"):
            return FirewallBackend.NFTABLES
        elif shutil.which("iptables"):
            return FirewallBackend.IPTABLES
        else:
            logger.warning("No firewall backend detected")
            return FirewallBackend.NONE
    
    async def apply_rules(self):
        """Apply firewall rules based on configuration"""
        try:
            if self.backend == FirewallBackend.NONE:
                logger.info("Firewall disabled, skipping rules")
                return
            
            logger.info(f"Applying firewall rules using {self.backend.value}")
            
            if self.backend == FirewallBackend.NFTABLES:
                await self._apply_nftables()
            elif self.backend == FirewallBackend.IPTABLES:
                await self._apply_iptables()
            elif self.backend == FirewallBackend.UFW:
                await self._apply_ufw()
            elif self.backend == FirewallBackend.FIREWALLD:
                await self._apply_firewalld()
            
            logger.info("Firewall rules applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply firewall rules: {e}")
            # Send alert
            from app.services.alerts import AlertService
            alert_service = AlertService()
            await alert_service.send_alert(
                "Firewall Configuration Failed",
                f"Failed to apply firewall rules: {e}",
                severity="error"
            )
            raise
    
    async def _apply_nftables(self):
        """Apply rules using nftables"""
        rules = self._generate_nftables_rules()
        
        # Write rules to file
        rules_file = "/etc/nftables/tor-proxy-pool.nft"
        with open(rules_file, 'w') as f:
            f.write(rules)
        
        # Apply rules
        subprocess.run(["nft", "-f", rules_file], check=True)
    
    def _generate_nftables_rules(self) -> str:
        """Generate nftables rules"""
        rules = []
        rules.append("#!/usr/sbin/nft -f")
        rules.append("")
        rules.append("table inet tor_proxy_pool {")
        
        # Panel whitelist
        if settings.PANEL_WHITELIST:
            rules.append("    set panel_whitelist {")
            rules.append("        type ipv4_addr")
            rules.append("        flags interval")
            rules.append("        elements = {")
            for ip in settings.PANEL_WHITELIST:
                rules.append(f"            {ip},")
            rules.append("        }")
            rules.append("    }")
        
        # SOCKS whitelist
        if settings.SOCKS_WHITELIST:
            rules.append("    set socks_whitelist {")
            rules.append("        type ipv4_addr")
            rules.append("        flags interval")
            rules.append("        elements = {")
            for ip in settings.SOCKS_WHITELIST:
                rules.append(f"            {ip},")
            rules.append("        }")
            rules.append("    }")
        
        rules.append("    chain input {")
        rules.append("        type filter hook input priority 0; policy drop;")
        rules.append("")
        rules.append("        # Allow loopback")
        rules.append("        iif lo accept")
        rules.append("")
        rules.append("        # Allow established connections")
        rules.append("        ct state established,related accept")
        rules.append("")
        
        # Panel access
        if settings.PANEL_WHITELIST:
            rules.append(f"        # Panel access (port {settings.PORT})")
            rules.append(f"        tcp dport {settings.PORT} ip saddr @panel_whitelist accept")
        else:
            rules.append(f"        # Panel access (port {settings.PORT}) - open")
            rules.append(f"        tcp dport {settings.PORT} accept")
        
        # SOCKS ports
        socks_port_range = f"{settings.TOR_BASE_SOCKS_PORT}-{settings.TOR_BASE_SOCKS_PORT + settings.TOR_POOL_SIZE - 1}"
        if settings.SOCKS_WHITELIST:
            rules.append(f"        # SOCKS ports ({socks_port_range})")
            rules.append(f"        tcp dport {socks_port_range} ip saddr @socks_whitelist accept")
        else:
            rules.append(f"        # SOCKS ports ({socks_port_range}) - open")
            rules.append(f"        tcp dport {socks_port_range} accept")
        
        # Block Tor control ports from external access
        ctrl_port_range = f"{settings.TOR_BASE_CTRL_PORT}-{settings.TOR_BASE_CTRL_PORT + settings.TOR_POOL_SIZE - 1}"
        rules.append(f"        # Block Tor control ports ({ctrl_port_range})")
        rules.append(f"        tcp dport {ctrl_port_range} ip saddr != 127.0.0.1 drop")
        
        # SSH (if needed)
        rules.append("        # SSH")
        rules.append("        tcp dport 22 accept")
        
        # ICMP
        rules.append("        # ICMP")
        rules.append("        icmp type echo-request limit rate 5/second accept")
        
        rules.append("    }")
        rules.append("}")
        
        return '\n'.join(rules)
    
    async def _apply_iptables(self):
        """Apply rules using iptables"""
        # Flush existing rules
        subprocess.run(["iptables", "-F"], check=True)
        
        # Default policies
        subprocess.run(["iptables", "-P", "INPUT", "DROP"], check=True)
        subprocess.run(["iptables", "-P", "FORWARD", "DROP"], check=True)
        subprocess.run(["iptables", "-P", "OUTPUT", "ACCEPT"], check=True)
        
        # Allow loopback
        subprocess.run(["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"], check=True)
        
        # Allow established
        subprocess.run(["iptables", "-A", "INPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"], check=True)
        
        # Panel access
        if settings.PANEL_WHITELIST:
            for ip in settings.PANEL_WHITELIST:
                subprocess.run([
                    "iptables", "-A", "INPUT", "-p", "tcp", "--dport", str(settings.PORT),
                    "-s", ip, "-j", "ACCEPT"
                ], check=True)
        else:
            subprocess.run([
                "iptables", "-A", "INPUT", "-p", "tcp", "--dport", str(settings.PORT),
                "-j", "ACCEPT"
            ], check=True)
        
        # SOCKS ports
        socks_port_range = f"{settings.TOR_BASE_SOCKS_PORT}:{settings.TOR_BASE_SOCKS_PORT + settings.TOR_POOL_SIZE - 1}"
        if settings.SOCKS_WHITELIST:
            for ip in settings.SOCKS_WHITELIST:
                subprocess.run([
                    "iptables", "-A", "INPUT", "-p", "tcp", "--dport", socks_port_range,
                    "-s", ip, "-j", "ACCEPT"
                ], check=True)
        else:
            subprocess.run([
                "iptables", "-A", "INPUT", "-p", "tcp", "--dport", socks_port_range,
                "-j", "ACCEPT"
            ], check=True)
        
        # Block control ports from external
        ctrl_port_range = f"{settings.TOR_BASE_CTRL_PORT}:{settings.TOR_BASE_CTRL_PORT + settings.TOR_POOL_SIZE - 1}"
        subprocess.run([
            "iptables", "-A", "INPUT", "-p", "tcp", "--dport", ctrl_port_range,
            "!", "-s", "127.0.0.1", "-j", "DROP"
        ], check=True)
        
        # SSH
        subprocess.run(["iptables", "-A", "INPUT", "-p", "tcp", "--dport", "22", "-j", "ACCEPT"], check=True)
        
        # ICMP
        subprocess.run(["iptables", "-A", "INPUT", "-p", "icmp", "--icmp-type", "echo-request", "-m", "limit", "--limit", "5/sec", "-j", "ACCEPT"], check=True)
        
        # Save rules
        subprocess.run(["iptables-save"], check=True, stdout=open("/etc/iptables/rules.v4", "w"))
    
    async def _apply_ufw(self):
        """Apply rules using UFW"""
        # Reset UFW
        subprocess.run(["ufw", "--force", "reset"], check=True)
        
        # Default policies
        subprocess.run(["ufw", "default", "deny", "incoming"], check=True)
        subprocess.run(["ufw", "default", "allow", "outgoing"], check=True)
        
        # SSH
        subprocess.run(["ufw", "allow", "22/tcp"], check=True)
        
        # Panel access
        if settings.PANEL_WHITELIST:
            for ip in settings.PANEL_WHITELIST:
                subprocess.run(["ufw", "allow", "from", ip, "to", "any", "port", str(settings.PORT), "proto", "tcp"], check=True)
        else:
            subprocess.run(["ufw", "allow", str(settings.PORT) + "/tcp"], check=True)
        
        # SOCKS ports
        for i in range(settings.TOR_POOL_SIZE):
            port = settings.TOR_BASE_SOCKS_PORT + i
            if settings.SOCKS_WHITELIST:
                for ip in settings.SOCKS_WHITELIST:
                    subprocess.run(["ufw", "allow", "from", ip, "to", "any", "port", str(port), "proto", "tcp"], check=True)
            else:
                subprocess.run(["ufw", "allow", str(port) + "/tcp"], check=True)
        
        # Enable UFW
        subprocess.run(["ufw", "--force", "enable"], check=True)
    
    async def _apply_firewalld(self):
        """Apply rules using firewalld"""
        # Create custom zone
        zone = "tor-proxy-pool"
        
        try:
            subprocess.run(["firewall-cmd", "--permanent", "--new-zone", zone], check=True)
        except subprocess.CalledProcessError:
            # Zone might already exist
            pass
        
        # Set default target
        subprocess.run(["firewall-cmd", "--permanent", "--zone", zone, "--set-target", "DROP"], check=True)
        
        # Add interface
        subprocess.run(["firewall-cmd", "--permanent", "--zone", zone, "--add-interface", "eth0"], check=True)
        
        # SSH
        subprocess.run(["firewall-cmd", "--permanent", "--zone", zone, "--add-service", "ssh"], check=True)
        
        # Panel port
        subprocess.run(["firewall-cmd", "--permanent", "--zone", zone, "--add-port", f"{settings.PORT}/tcp"], check=True)
        
        # Panel whitelist
        if settings.PANEL_WHITELIST:
            for ip in settings.PANEL_WHITELIST:
                subprocess.run(["firewall-cmd", "--permanent", "--zone", zone, "--add-source", ip], check=True)
        
        # SOCKS ports
        socks_port_range = f"{settings.TOR_BASE_SOCKS_PORT}-{settings.TOR_BASE_SOCKS_PORT + settings.TOR_POOL_SIZE - 1}"
        subprocess.run(["firewall-cmd", "--permanent", "--zone", zone, "--add-port", f"{socks_port_range}/tcp"], check=True)
        
        # Reload
        subprocess.run(["firewall-cmd", "--reload"], check=True)
    
    async def test_rules(self) -> bool:
        """Test if firewall rules are working"""
        try:
            # Basic connectivity test
            result = subprocess.run(
                ["ping", "-c", "1", "8.8.8.8"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Firewall test failed: {e}")
            return False
