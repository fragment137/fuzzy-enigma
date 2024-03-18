import subprocess

def gcloud_command(command):
    """Run a gcloud command and return its output."""
    try:
        print(f"Executing command: {' '.join(command)}")  # Verbose output before executing
        output = subprocess.check_output(["gcloud"] + command, text=True)
        print(f"Command succeeded: {' '.join(command)}")
        return output
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(command)}\nError: {e}")
        return None

def main():
    certs = []

    # Prompt for user input instead of reading from CSV
    full_domain = input("Enter full domain (e.g., example.com): ")
    subdomain = input("Enter subdomains, comma delimited (e.g., www,api): ")
    project_name = input("Enter project name: ")
    service_name = input("Enter service name: ")
    region = input("Enter a region")

    #subdomains = subdomains-input.split(',')
    domain = full_domain.split('.')[0]
    #object_prefixes = [f"{subdomain}-{domain}" for subdomain in subdomains]
    object_prefix = f"{subdomain}-{domain}"

    print(f"Creating Serverless NEG for {subdomain}.{full_domain}")
    # Create Serverless NEG
    gcloud_command([
        "compute", "network-endpoint-groups", "create",
        f"{object_prefix}-serverless-neg",
        "--region=" + region,
        "--network-endpoint-type=SERVERLESS",
        "--app-engine-app=" + service_name
    ])

    print(f"Creating Backend Service for {subdomain}.{full_domain}")
    # Create Backend Service
    backend_service_name = f"{object_prefix}-backend-service"
    gcloud_command([
        "compute", "backend-services", "create", backend_service_name,
        "--global"
    ])

    print(f"Adding Backend to the NEG for {subdomain}.{full_domain}")
    # Add the Backend to the NEG
    gcloud_command([
        "compute", "backend-services", "add-backend", backend_service_name,
        "--global",
        "--network-endpoint-group=" + f"{object_prefix}-serverless-neg",
        "--network-endpoint-group-region=" + region
    ])
    
    # Create SSL certificates and add to certs list
    ssl_cert_name = f"{object_prefix}-ssl-cert"
    full_domain_for_cert = f"{subdomain}.{full_domain}"
    print(f"Creating SSL Certificates for {full_domain_for_cert}")
    if not gcloud_command(["compute", "ssl-certificates", "describe", f"{domain}-ssl-cert"]):
        gcloud_command(["compute", "ssl-certificates", "create", f"{domain}-ssl-cert", "--domains=" + full_domain])
    gcloud_command([
        "compute", "ssl-certificates", "create", ssl_cert_name,
        "--domains=" + full_domain_for_cert
    ])
    certs.append(ssl_cert_name)

    print(f"Adding Path Matcher to the URL Map for {subdomain}.{full_domain}")
    # Add a path matcher to the URL map
    url_map_name = f"{project_name}-https-url-map"
    # Check if URL map exists, if not, create it
    if not gcloud_command(["compute", "url-maps", "describe", url_map_name]):
        gcloud_command(["compute", "url-maps", "create", url_map_name, "--default-service", backend_service_name])
    gcloud_command([
        "compute", "url-maps", "add-path-matcher", url_map_name,
        "--path-matcher-name=" + f"{object_prefix}-path-matcher",
        "--default-service", backend_service_name,
        "--new-hosts=" + f"{subdomain}.{full_domain}"
    ])

    print(f"Updating HTTPS Proxy with SSL certificates for project {project_name}")
    # Update HTTPS proxy with SSL certificates
    https_proxy_name = f"{project_name}-https-proxy"
    if not gcloud_command(["compute", "target-https-proxies", "describe", https_proxy_name]):
        gcloud_command(["compute", "target-https-proxies", "create", https_proxy_name, "--url-map", url_map_name, --"ssl-certificates=" + ",".join(certs)])
    gcloud_command([
        "compute", "target-https-proxies", "update", https_proxy_name,
        "--ssl-certificates=" + ",".join(certs)
    ])
    # Step 1: Create a Global Static IP Address
    ip_name = f"{project_name}-global-ip"
    print(f"Creating Global Static IP Address named {ip_name}")
    gcloud_command([
        "compute", "addresses", "create", ip_name,
        "--global",
        "--ip-version=IPV4"
    ])

    # Step 2: Create a Global Forwarding Rule to connect the IP with the HTTPS proxy
    print(f"Creating Global Forwarding Rule for IP {ip_name} and HTTPS Proxy {https_proxy_name}")
    gcloud_command([
        "compute", "forwarding-rules", "create", f"{project_name}-https-forwarding-rule",
        "--global",
        "--target-https-proxy", https_proxy_name,
        "--address", ip_name,
        "--ports", "443"
    ])
    # Step 1: Create an HTTP URL map for redirecting all traffic to HTTPS
    http_url_map_name = f"{project_name}-http-url-map"
    print(f"Creating HTTP URL Map for redirecting to HTTPS named {http_url_map_name}")
    gcloud_command([
        "compute", "url-maps", "create", http_url_map_name,
        "--default-redirect-action", f"\"https-redirect,strip-query=false,https-redirect-code=MOVED_PERMANENTLY_DEFAULT, prefix-redirect='https://{full_domain}'\""
    ])

    # Step 2: Create a target HTTP proxy using the HTTP URL map
    http_proxy_name = f"{project_name}-http-proxy"
    print(f"Creating Target HTTP Proxy named {http_proxy_name}")
    gcloud_command([
        "compute", "target-http-proxies", "create", http_proxy_name,
        "--url-map", http_url_map_name
    ])

    # Step 3: Create a global forwarding rule to redirect HTTP to HTTPS
    http_forwarding_rule_name = f"{project_name}-http-forwarding-rule"
    print(f"Creating Global Forwarding Rule for HTTP named {http_forwarding_rule_name}")
    gcloud_command([
        "compute", "forwarding-rules", "create", http_forwarding_rule_name,
        "--global",
        "--target-http-proxy", http_proxy_name,
        "--ports", "80"
    ])

if __name__ == "__main__":
    main()
