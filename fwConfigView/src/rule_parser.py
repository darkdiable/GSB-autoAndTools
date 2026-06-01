import csv
import json
import ipaddress
from typing import List, Dict, Union, Optional


class Rule:
    def __init__(self, rule_data: Dict):
        self.id = str(rule_data["id"])
        self.priority = int(rule_data["priority"])
        self.src_ip = str(rule_data["src_ip"])
        self.dst_ip = str(rule_data["dst_ip"])
        self.protocol = str(rule_data["protocol"]).lower()
        self.port = str(rule_data["port"])
        self.action = str(rule_data["action"]).lower()
        self.hit_count = 0
        self.total_match_time = 0.0
        self.match_times: List[float] = []
        self._parse_ports()
        self._validate()

    def _parse_ports(self) -> None:
        if self.port.lower() == "any":
            self.port_start = 0
            self.port_end = 65535
            self.port_any = True
        elif "-" in self.port:
            parts = self.port.split("-")
            self.port_start = int(parts[0].strip())
            self.port_end = int(parts[1].strip())
            self.port_any = False
        else:
            self.port_start = int(self.port)
            self.port_end = int(self.port)
            self.port_any = False

    def _validate(self) -> None:
        if self.protocol not in ("tcp", "udp", "icmp", "any"):
            raise ValueError(f"Invalid protocol: {self.protocol}")
        if self.action not in ("allow", "deny"):
            raise ValueError(f"Invalid action: {self.action}")
        try:
            if "/" in self.src_ip:
                ipaddress.ip_network(self.src_ip, strict=False)
            else:
                ipaddress.ip_address(self.src_ip)
        except ValueError as e:
            raise ValueError(f"Invalid src_ip {self.src_ip}: {e}")
        try:
            if "/" in self.dst_ip:
                ipaddress.ip_network(self.dst_ip, strict=False)
            else:
                ipaddress.ip_address(self.dst_ip)
        except ValueError as e:
            raise ValueError(f"Invalid dst_ip {self.dst_ip}: {e}")
        if not self.port_any:
            if not (0 <= self.port_start <= 65535 and 0 <= self.port_end <= 65535):
                raise ValueError(f"Port out of range: {self.port}")
            if self.port_start > self.port_end:
                raise ValueError(f"Invalid port range: {self.port}")

    def matches_port(self, port: int) -> bool:
        return self.port_start <= port <= self.port_end

    def matches_protocol(self, protocol: str) -> bool:
        if self.protocol == "any":
            return True
        return self.protocol == protocol.lower()

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "priority": self.priority,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "protocol": self.protocol,
            "port": self.port,
            "action": self.action,
        }

    def avg_match_time(self) -> float:
        if self.match_times:
            return sum(self.match_times) / len(self.match_times)
        return 0.0


def parse_csv(file_path: str) -> List[Rule]:
    rules = []
    with open(file_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rules.append(Rule(row))
    rules.sort(key=lambda r: r.priority)
    return rules


def parse_json(file_path: str) -> List[Rule]:
    with open(file_path, "r") as f:
        data = json.load(f)
    rules = [Rule(item) for item in data]
    rules.sort(key=lambda r: r.priority)
    return rules


def load_rules(file_path: str) -> List[Rule]:
    if file_path.lower().endswith(".csv"):
        return parse_csv(file_path)
    elif file_path.lower().endswith(".json"):
        return parse_json(file_path)
    else:
        raise ValueError("Unsupported file format. Use .csv or .json")


def export_rules_to_json(rules: List[Rule], file_path: str) -> None:
    data = [r.to_dict() for r in rules]
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def create_implicit_deny_rule() -> Rule:
    return Rule({
        "id": "implicit_deny",
        "priority": 999999,
        "src_ip": "0.0.0.0/0",
        "dst_ip": "0.0.0.0/0",
        "protocol": "any",
        "port": "any",
        "action": "deny",
    })
