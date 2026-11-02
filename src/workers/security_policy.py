"""Browser Security and Navigation Policy for PriceWise AI Beauty (Phase 6A).

Enforces strict URL validation, retailer domain allowlisting, and SSRF prevention
for Playwright browser workers.

Guarantees:
1. HTTPS-only navigation.
2. Explicit retailer domain allowlisting (Nykaa, Tira, Purplle, Amazon India, Myntra).
3. Private IP & loopback blocking (127.0.0.1, localhost, 10.*, 192.168.*, 172.16-31.*).
4. Cloud metadata endpoint blocking (169.254.169.254).
5. Rejection of arbitrary user-submitted URLs.
"""

import ipaddress
import socket
from typing import Optional
from urllib.parse import urlparse

# Explicitly allowed retailer domains
ALLOWED_RETAILER_DOMAINS = {
    "nykaa.com",
    "tirabeauty.com",
    "purplle.com",
    "amazon.in",
    "myntra.com",
}

# Private / reserved subnets that browser workers must NEVER access (SSRF Protection)
BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("10.0.0.0/8"),       # Private class A
    ipaddress.ip_network("172.16.0.0/12"),    # Private class B
    ipaddress.ip_network("192.168.0.0/16"),   # Private class C
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local & Cloud Metadata (AWS/GCP/Azure)
    ipaddress.ip_network("0.0.0.0/8"),        # This host
    ipaddress.ip_network("::1/128"),          # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 Unique Local
    ipaddress.ip_network("fe80::/10"),        # IPv6 Link-Local
]


def is_ip_blocked(ip_str: str) -> bool:
    """Check whether an IP address belongs to any private, loopback, or cloud metadata network."""
    try:
        ip = ipaddress.ip_address(ip_str)
        for net in BLOCKED_NETWORKS:
            if ip in net:
                return True
        return False
    except ValueError:
        return False


def validate_browser_url(url: str, check_dns: bool = False) -> tuple[bool, Optional[str]]:
    """
    Validate that a URL is safe for headless browser navigation.
    Returns (is_valid, rejection_reason).
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"

    url_clean = url.strip()
    try:
        parsed = urlparse(url_clean)
    except Exception as e:
        return False, f"Malformed URL: {e}"

    # 1. Enforce HTTPS scheme (reject http://, file://, ftp://, javascript:)
    if parsed.scheme.lower() != "https":
        return False, f"Insecure scheme '{parsed.scheme}'. Only HTTPS is permitted."

    hostname = (parsed.hostname or "").lower().strip()
    if not hostname:
        return False, "Missing hostname in URL"

    # 2. Block direct loopback / localhost names
    if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"):
        return False, f"Access to localhost/internal host '{hostname}' is strictly forbidden."

    # 3. Check if hostname is a raw IP address
    try:
        ip = ipaddress.ip_address(hostname)
        if is_ip_blocked(str(ip)):
            return False, f"Navigation to private/cloud metadata IP '{hostname}' is blocked."
        return False, "Direct IP navigation is not allowed; must use approved domain name."
    except ValueError:
        pass  # Hostname is a domain name, proceed

    # 4. Check domain allowlist
    is_allowed_domain = False
    for allowed in ALLOWED_RETAILER_DOMAINS:
        if hostname == allowed or hostname.endswith(f".{allowed}"):
            is_allowed_domain = True
            break

    if not is_allowed_domain:
        return False, (
            f"Domain '{hostname}' is not in the approved retailer allowlist "
            f"({', '.join(sorted(ALLOWED_RETAILER_DOMAINS))})."
        )

    # 5. Optional DNS resolution check (prevent DNS rebinding to private IPs)
    if check_dns:
        try:
            resolved_ips = socket.gethostbyname_ex(hostname)[2]
            for r_ip in resolved_ips:
                if is_ip_blocked(r_ip):
                    return False, f"Domain '{hostname}' resolved to blocked IP '{r_ip}'."
        except Exception as e:
            return False, f"DNS resolution failed for '{hostname}': {e}"

    return True, None

