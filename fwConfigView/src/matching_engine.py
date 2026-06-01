import ipaddress
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from .rule_parser import Rule, create_implicit_deny_rule


@dataclass
class Packet:
    src_ip: str
    dst_ip: str
    protocol: str
    port: int
    matched_rule_id: Optional[str] = None
    match_time_us: float = 0.0


class MatchingEngine:
    def __init__(self, rules: List[Rule]):
        self.rules = rules[:]
        self.implicit_deny = create_implicit_deny_rule()
        self._preprocess_networks()

    def _preprocess_networks(self) -> None:
        self._rule_networks = {}
        for rule in self.rules:
            if "/" in rule.src_ip:
                self._rule_networks[(rule.id, "src")] = ipaddress.ip_network(rule.src_ip, strict=False)
            else:
                self._rule_networks[(rule.id, "src")] = ipaddress.ip_network(f"{rule.src_ip}/32", strict=False)
            if "/" in rule.dst_ip:
                self._rule_networks[(rule.id, "dst")] = ipaddress.ip_network(rule.dst_ip, strict=False)
            else:
                self._rule_networks[(rule.id, "dst")] = ipaddress.ip_network(f"{rule.dst_ip}/32", strict=False)

        if "/" in self.implicit_deny.src_ip:
            self._rule_networks[(self.implicit_deny.id, "src")] = ipaddress.ip_network(
                self.implicit_deny.src_ip, strict=False
            )
        if "/" in self.implicit_deny.dst_ip:
            self._rule_networks[(self.implicit_deny.id, "dst")] = ipaddress.ip_network(
                self.implicit_deny.dst_ip, strict=False
            )

    def _match_single_rule(self, packet: Packet, rule: Rule) -> Tuple[bool, float]:
        start = time.perf_counter()
        try:
            src_addr = ipaddress.ip_address(packet.src_ip)
            dst_addr = ipaddress.ip_address(packet.dst_ip)
            src_net = self._rule_networks[(rule.id, "src")]
            dst_net = self._rule_networks[(rule.id, "dst")]
            if src_addr in src_net and dst_addr in dst_net:
                if rule.matches_protocol(packet.protocol):
                    if rule.matches_port(packet.port):
                        elapsed = (time.perf_counter() - start) * 1_000_000
                        return True, elapsed
        except ValueError:
            pass
        elapsed = (time.perf_counter() - start) * 1_000_000
        return False, elapsed

    def match_packet(self, packet: Packet) -> Tuple[Optional[Rule], float]:
        total_time = 0.0
        for rule in self.rules:
            matched, match_time = self._match_single_rule(packet, rule)
            total_time += match_time
            rule.total_match_time += match_time
            rule.match_times.append(match_time)
            if matched:
                rule.hit_count += 1
                packet.matched_rule_id = rule.id
                packet.match_time_us = total_time
                return rule, total_time

        matched, match_time = self._match_single_rule(packet, self.implicit_deny)
        total_time += match_time
        self.implicit_deny.total_match_time += match_time
        self.implicit_deny.match_times.append(match_time)
        if matched:
            self.implicit_deny.hit_count += 1
            packet.matched_rule_id = self.implicit_deny.id
            packet.match_time_us = total_time
            return self.implicit_deny, total_time

        packet.match_time_us = total_time
        return None, total_time

    def match_packets(self, packets: List[Packet]) -> List[Tuple[Optional[Rule], float]]:
        results = []
        for packet in packets:
            result = self.match_packet(packet)
            results.append(result)
        return results

    def get_all_rules(self) -> List[Rule]:
        return self.rules + [self.implicit_deny]

    def get_average_match_time(self) -> float:
        all_rules = self.get_all_rules()
        all_times = []
        for rule in all_rules:
            all_times.extend(rule.match_times)
        if all_times:
            return sum(all_times) / len(all_times)
        return 0.0

    def get_statistics(self) -> Dict:
        all_rules = self.get_all_rules()
        allow_count = sum(r.hit_count for r in all_rules if r.action == "allow")
        deny_count = sum(r.hit_count for r in all_rules if r.action == "deny")
        implicit_hits = self.implicit_deny.hit_count

        protocol_hits = {"tcp": {"allow": 0, "deny": 0}, "udp": {"allow": 0, "deny": 0}, "icmp": {"allow": 0, "deny": 0}}
        for rule in all_rules:
            if rule.hit_count > 0:
                proto = rule.protocol
                if proto == "any":
                    for p in protocol_hits:
                        protocol_hits[p][rule.action] += rule.hit_count
                elif proto in protocol_hits:
                    protocol_hits[proto][rule.action] += rule.hit_count

        return {
            "total_rules": len(self.rules),
            "allow_count": allow_count,
            "deny_count": deny_count,
            "implicit_deny_hits": implicit_hits,
            "average_match_time_us": self.get_average_match_time(),
            "protocol_hits": protocol_hits,
        }
