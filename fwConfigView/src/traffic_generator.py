import random
import ipaddress
from typing import List, Optional
from .matching_engine import Packet


class TrafficGenerator:
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.protocols = ["tcp", "udp", "icmp"]

    def _generate_ip(self, ip_spec: Optional[str] = None) -> str:
        if ip_spec is None:
            return ".".join(str(random.randint(0, 255)) for _ in range(4))
        if "/" in ip_spec:
            network = ipaddress.ip_network(ip_spec, strict=False)
            hosts = list(network.hosts())
            if not hosts:
                return str(network.network_address)
            return str(random.choice(hosts))
        return ip_spec

    def generate_packet(
        self,
        protocol: Optional[str] = None,
        port_range: Optional[tuple] = None,
        src_ip: Optional[str] = None,
        dst_ip: Optional[str] = None,
    ) -> Packet:
        if protocol is None:
            protocol = random.choice(self.protocols)
        protocol = protocol.lower()

        if port_range is None:
            port = random.randint(1, 65535)
        else:
            port = random.randint(port_range[0], port_range[1])

        src_ip_str = self._generate_ip(src_ip)
        dst_ip_str = self._generate_ip(dst_ip)

        return Packet(
            src_ip=src_ip_str,
            dst_ip=dst_ip_str,
            protocol=protocol,
            port=port,
        )

    def generate_packets(
        self,
        count: int = 500,
        protocol: Optional[str] = None,
        port_range: Optional[tuple] = None,
        src_ip: Optional[str] = None,
        dst_ip: Optional[str] = None,
    ) -> List[Packet]:
        packets = []
        for _ in range(count):
            packets.append(
                self.generate_packet(
                    protocol=protocol,
                    port_range=port_range,
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                )
            )
        return packets

    def generate_random_rules(self, count: int = 20000) -> List[dict]:
        rules = []
        actions = ["allow", "deny"]
        for i in range(count):
            rule = {
                "id": f"rule_{i+1:05d}",
                "priority": random.randint(1, 100000),
                "src_ip": self._random_cidr(),
                "dst_ip": self._random_cidr(),
                "protocol": random.choice(self.protocols),
                "port": self._random_port_spec(),
                "action": random.choice(actions),
            }
            rules.append(rule)
        return rules

    def _random_cidr(self) -> str:
        if random.random() < 0.3:
            return ".".join(str(random.randint(0, 255)) for _ in range(4))
        ip = ".".join(str(random.randint(0, 255)) for _ in range(4))
        prefix = random.randint(8, 32)
        return f"{ip}/{prefix}"

    def _random_port_spec(self) -> str:
        r = random.random()
        if r < 0.2:
            return "any"
        elif r < 0.5:
            start = random.randint(1, 65000)
            end = random.randint(start, min(start + 100, 65535))
            return f"{start}-{end}"
        else:
            return str(random.randint(1, 65535))
