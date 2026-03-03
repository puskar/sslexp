import ssl
import socket
import argparse
from datetime import datetime, timezone
from OpenSSL import crypto
from pathlib import Path
import subprocess
import sys

def get_tls_expiration_date(domain):
    context = ssl.create_default_context()
    with socket.create_connection((domain, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            cert = ssock.getpeercert()
            expiration_date_str = cert['notAfter']
            expiration_date = datetime.strptime(expiration_date_str, '%b %d %H:%M:%S %Y %Z')
            return expiration_date

def get_tls_expiration_date_from_file(cert_file_path):
    with open(cert_file_path, 'rb') as cert_file:
        cert_data = cert_file.read()
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)
        expiration_date_str = cert.get_notAfter().decode('ascii')
        expiration_date = datetime.strptime(expiration_date_str, '%Y%m%d%H%M%SZ')
        return expiration_date

def compare_dates(expiration_date):
    current_date = datetime.now(timezone.utc).replace(tzinfo=None)
    if expiration_date > current_date:
        print(f"The TLS certificate is valid until {expiration_date}.")
    else:
        print(f"The TLS certificate has expired on {expiration_date}.")

def compare_certificates(domain_expiration_date, file_expiration_date):
    if domain_expiration_date > file_expiration_date:
        print("The remote certificate for the domain is valid longer than the certificate in the file.")
        return 0
    elif domain_expiration_date < file_expiration_date:
        print("The certificate in the file is valid longer than the remote certificate for the domain.")
        return 3
    else:
        print(f"Both certificates have the same expiration date: {domain_expiration_date}.")
        return 2
        
def update_certs(domain, local_path, remote_path):
    
    cmd=f"sudo scp -r {local_path}/*.pem root@{domain}:{remote_path}"
    
    print(f"Running command: {cmd}")
    if not Path(local_path).exists():
        print(f"Local certificate file {local_path} does not exist.")
        return
    
    try:        subprocess.run(['ssh', f'root@{domain}', f'test -d {remote_path}'], check=True)  
    except subprocess.CalledProcessError:
        print(f"Remote certificates file {remote_path} does not exist.")
        return

    print(f"Updating certificate on {domain} from {local_path} to {remote_path}...")

    try:
        subprocess.run(cmd, shell=True, check=True)
        print("Certificates updated successfully.")
    except subprocess.CalledProcessError:
        print("Failed to update certificates.")
        
    try:
        subprocess.run(['ssh', f'root@{domain}', 'systemctl restart nginx'], check=True)  
        print(f"Nginx restarted successfully on {domain}.")
    except subprocess.CalledProcessError:
        print(f"Failed to restart Nginx on {domain}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check TLS certificate expiration dates.")
    parser.add_argument("--domain", help="Check the expiration date of a domain's TLS certificate.")
    parser.add_argument("--file", help="Check the expiration date of a certificate file.")
    parser.add_argument("--compare", nargs=2, metavar=('DOMAIN', 'FILE'), help="Compare the expiration dates of a domain's TLS certificate and a certificate file.")
    parser.add_argument("--update", nargs=3, metavar=  ('DOMAIN', 'LOCAL_PATH', 'REMOTE_PATH'), help="Update the certificate from local path to remote path.")
    
    args = parser.parse_args()

    if args.domain:
        expiration_date = get_tls_expiration_date(args.domain)
        compare_dates(expiration_date)
    elif args.file:
        expiration_date = get_tls_expiration_date_from_file(args.file)
        compare_dates(expiration_date)
    elif args.compare:
        domain_expiration_date = get_tls_expiration_date(args.compare[0])
        file_expiration_date = get_tls_expiration_date_from_file(args.compare[1])
        sys.exit(compare_certificates(domain_expiration_date, file_expiration_date))
    elif args.update:
        update_certs(args.update[0], args.update[1], args.update[2])
    else:
        choice = input("Do you want to check a domain, a certificate file, or update certificates? (domain/file/update): ").strip().lower()
        if choice == "domain":
            domain = input("Enter the domain: ")
            expiration_date = get_tls_expiration_date(domain)
            compare_dates(expiration_date)
        elif choice == "file":
            cert_file_path = input("Enter the certificate file path: ")
            expiration_date = get_tls_expiration_date_from_file(cert_file_path)
            compare_dates(expiration_date)
        elif choice == "update":
            domain = input("Enter the domain: ")
            local_path = input("Enter the local certificate path: ")
            remote_path = input("Enter the remote certificate path: ")
            update_certs(domain, local_path, remote_path)
        elif choice == "compare":
            domain = input("Enter the domain: ")
            cert_file_path = input("Enter the certificate file path: ")
            domain_expiration_date = get_tls_expiration_date(domain)
            file_expiration_date = get_tls_expiration_date_from_file(cert_file_path)
            compare_certificates(domain_expiration_date, file_expiration_date)
        else:
            print("Invalid choice.")
            exit(1)