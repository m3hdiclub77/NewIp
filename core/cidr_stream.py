import random
import ipaddress

class CIDRStream:
    def __init__(self, cidrs, limit):
        self.cidrs = cidrs
        self.limit = limit

    def stream(self):
        random.shuffle(self.cidrs)

        per_source = {}

        for cidr in self.cidrs:
            try:
                network = ipaddress.ip_network(cidr, strict=False)
                src = str(network.network_address)

                if src not in per_source:
                    per_source[src] = []

                for ip in network.hosts():
                    if len(per_source[src]) >= self.limit:
                        break
                    ip_str = str(ip)
                    per_source[src].append(ip_str)
                    yield ip_str

            except Exception as e:
                print(f"Error processing {cidr}: {e}")
                continue
