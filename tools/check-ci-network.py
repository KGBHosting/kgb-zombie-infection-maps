#!/usr/bin/env python3
"""Read-only diagnostics. Print fixed public-host outcomes, never network data."""
import json, os, subprocess, urllib.request

proxy_keys = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "all_proxy", "no_proxy")
record = {"proxy_environment_present": {key: bool(os.environ.get(key)) for key in proxy_keys}}
for host in ("archive.ubuntu.com", "security.ubuntu.com", "azure.archive.ubuntu.com"):
    try:
        dns = subprocess.run(["getent", "ahosts", host], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        dns = False
    try:
        request = urllib.request.Request("https://" + host + "/ubuntu/dists/noble/InRelease", method="HEAD")
        with urllib.request.urlopen(request, timeout=8) as response:
            https = response.status == 200
    except Exception:
        # No exception message, response, proxy URL or resolver data may escape.
        https = False
    record[host] = {"host_dns_success": dns, "host_https_success": https}
print(json.dumps(record, sort_keys=True))
