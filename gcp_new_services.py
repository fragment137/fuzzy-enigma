import csv
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

def main(csv_filename):
    certs = []

    with open(csv_filename, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            domain = row['full_domain'].split('.')[0]
            subdomain = row['subdomain']
            project_name = row['project_name']
            service_name = row['service_name']

            object_prefix = f"{subdomain}-{domain}"

            print(f"Creating Serverless NEG for {subdomain}.{row['full_domain']}")
            # Create Serverless NEG
            gcloud_command([
                "compute", "network-endpoint-groups", "create",
                f"{object_prefix}-serverless-neg",
                "--region=northamerica-northeast1",
                "--network-endpoint-type=SERVERLESS",
                "--cloud-run-service=" + service_name
            ])

            print(f"Creating Backend Service for {subdomain}.{row['full_domain']}")
            # Create Backend Service
            backend_service_name = f"{object_prefix}-backend-service"
            gcloud_command([
                "compute", "backend-services", "create", backend_service_name,
                "--global"
            ])

            print(f"Adding Backend to the NEG for {subdomain}.{row['full_domain']}")
            # Add the Backend to the NEG
            gcloud_command([
                "compute", "backend-services", "add-backend", backend_service_name,
                "--global",
                "--network-endpoint-group=" + f"{object_prefix}-serverless-neg",
                "--network-endpoint-group-region=northamerica-northeast1"
            ])

            
            # Create SSL certificate and add to certs list
            ssl_cert_name = f"{object_prefix}-ssl-cert"
            full_domain_for_cert = f"{row['subdomain']}.{row['full_domain']}"
            print(f"Creating SSL Certificate for {full_domain_for_cert}")
            gcloud_command([
                "compute", "ssl-certificates", "create", ssl_cert_name,
                "--domains=" + full_domain_for_cert
            ])
            certs.append(ssl_cert_name)

            print(f"Adding Path Matcher to the URL Map for {subdomain}.{row['full_domain']}")
            # Add a path matcher to the URL map
            url_map_name = f"{project_name}-https-url-map"
            # Check if URL map exists, if not, create it
            if not gcloud_command(["compute", "url-maps", "describe", url_map_name]):
                gcloud_command(["compute", "url-maps", "create", url_map_name, "--default-service", backend_service_name])
            gcloud_command([
                "compute", "url-maps", "add-path-matcher", url_map_name,
                "--path-matcher-name=" + f"{object_prefix}-path-matcher",
                "--default-service", backend_service_name,
                "--new-hosts=" + f"{subdomain}.{row['full_domain']}"
            ])

    print(f"Updating HTTPS Proxy with SSL certificates for project {project_name}")
    # Update HTTPS proxy with SSL certificates
    https_proxy_name = f"{project_name}-https-proxy"
    if not gcloud_command(["compute", "target-https-proxies", "describe", https_proxy_name]):
        gcloud_command(["compute", "target-https-proxies", "create", https_proxy_name, "--url-map", url_map_name])
    gcloud_command([
        "compute", "target-https-proxies", "update", https_proxy_name,
        "--ssl-certificates=" + ",".join(certs)
    ])

if __name__ == "__main__":
    csv_filename = "resources.csv"
    main(csv_filename)
