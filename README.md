## certificate tools

### sslexp.py

```
usage: sslexp.py [-h] [--domain DOMAIN] [--file FILE] [--compare DOMAIN FILE]

Check TLS certificate expiration dates.

options:
  -h, --help            show this help message and exit
  --domain DOMAIN       Check the expiration date of a domain's TLS certificate.
  --file FILE           Check the expiration date of a certificate file.
  --compare DOMAIN FILE
                        Compare the expiration dates of a domain's TLS certificate and a certificate file.
```

### cert_cal.py

Runs a flask server that you can use to generate a calendar feed of hostnames given in the URL.

e.g. `curl -s http://localhost:8093/certcal/142.251.45.179,slashbot.org,reddit.com,api.puskar.net,nogginbuster`

This will:

* ignore the ip address `142.251.45.179`, as we take hostnames only
* skip `slasbot.org`, as it does not respond on 443
* generate a calendar entry and 1 week alarm for both `reddit.com` and `api.puskar.net`
* skip `nogginbuster`, as it is not a FQDN and does not exist
