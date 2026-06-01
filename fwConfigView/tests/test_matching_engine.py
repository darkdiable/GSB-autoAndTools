import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rule_parser import Rule
from src.matching_engine import MatchingEngine, Packet


def create_test_rules():
    return [
        Rule({
            "id": "r1", "priority": 10,
            "src_ip": "192.168.1.0/24", "dst_ip": "10.0.0.0/8",
            "protocol": "tcp", "port": "80", "action": "allow"
        }),
        Rule({
            "id": "r2", "priority": 20,
            "src_ip": "192.168.0.0/16", "dst_ip": "10.0.0.5",
            "protocol": "tcp", "port": "22", "action": "deny"
        }),
        Rule({
            "id": "r3", "priority": 30,
            "src_ip": "10.0.0.0/8", "dst_ip": "0.0.0.0/0",
            "protocol": "icmp", "port": "any", "action": "allow"
        }),
    ]


def test_cidr_matching_inside_subnet():
    rules = create_test_rules()
    engine = MatchingEngine(rules)

    packet = Packet(
        src_ip="192.168.1.100",
        dst_ip="10.0.0.10",
        protocol="tcp",
        port=80
    )
    matched_rule, time = engine.match_packet(packet)
    assert matched_rule is not None
    assert matched_rule.id == "r1"
    assert matched_rule.hit_count == 1


def test_cidr_matching_outside_subnet():
    rules = create_test_rules()
    engine = MatchingEngine(rules)

    packet = Packet(
        src_ip="192.168.2.100",
        dst_ip="10.0.0.10",
        protocol="tcp",
        port=80
    )
    matched_rule, time = engine.match_packet(packet)
    assert matched_rule is not None
    assert matched_rule.id == "implicit_deny"


def test_single_ip_matching():
    rules = create_test_rules()
    engine = MatchingEngine(rules)

    packet = Packet(
        src_ip="192.168.50.100",
        dst_ip="10.0.0.5",
        protocol="tcp",
        port=22
    )
    matched_rule, time = engine.match_packet(packet)
    assert matched_rule is not None
    assert matched_rule.id == "r2"


def test_single_ip_not_matching():
    rules = create_test_rules()
    engine = MatchingEngine(rules)

    packet = Packet(
        src_ip="192.168.50.100",
        dst_ip="10.0.0.6",
        protocol="tcp",
        port=22
    )
    matched_rule, time = engine.match_packet(packet)
    assert matched_rule is not None
    assert matched_rule.id == "implicit_deny"


def test_protocol_matching():
    rules = create_test_rules()
    engine = MatchingEngine(rules)

    packet = Packet(
        src_ip="192.168.1.100",
        dst_ip="10.0.0.10",
        protocol="udp",
        port=80
    )
    matched_rule, time = engine.match_packet(packet)
    assert matched_rule is not None
    assert matched_rule.id == "implicit_deny"


def test_port_not_matching():
    rules = create_test_rules()
    engine = MatchingEngine(rules)

    packet = Packet(
        src_ip="192.168.1.100",
        dst_ip="10.0.0.10",
        protocol="tcp",
        port=81
    )
    matched_rule, time = engine.match_packet(packet)
    assert matched_rule is not None
    assert matched_rule.id == "implicit_deny"


def test_icmp_any_port():
    rules = create_test_rules()
    engine = MatchingEngine(rules)

    packet = Packet(
        src_ip="10.0.0.50",
        dst_ip="192.168.1.1",
        protocol="icmp",
        port=0
    )
    matched_rule, time = engine.match_packet(packet)
    assert matched_rule is not None
    assert matched_rule.id == "r3"
    assert engine.implicit_deny.hit_count == 0


def test_priority_order():
    rules = [
        Rule({
            "id": "high_priority", "priority": 5,
            "src_ip": "0.0.0.0/0", "dst_ip": "0.0.0.0/0",
            "protocol": "any", "port": "any", "action": "deny"
        }),
        Rule({
            "id": "low_priority", "priority": 100,
            "src_ip": "0.0.0.0/0", "dst_ip": "0.0.0.0/0",
            "protocol": "any", "port": "any", "action": "allow"
        }),
    ]
    engine = MatchingEngine(rules)

    packet = Packet(
        src_ip="1.2.3.4",
        dst_ip="5.6.7.8",
        protocol="tcp",
        port=80
    )
    matched_rule, time = engine.match_packet(packet)
    assert matched_rule is not None
    assert matched_rule.id == "high_priority"
    assert matched_rule.action == "deny"


def test_implicit_deny_counts_separately():
    rules = create_test_rules()
    engine = MatchingEngine(rules)

    for i in range(5):
        packet = Packet(
            src_ip=f"1.2.3.{i}",
            dst_ip=f"5.6.7.{i}",
            protocol="tcp",
            port=999
        )
        engine.match_packet(packet)

    stats = engine.get_statistics()
    assert stats["implicit_deny_hits"] == 5
    assert engine.implicit_deny.hit_count == 5


def test_match_time_recorded():
    rules = create_test_rules()
    engine = MatchingEngine(rules)

    packet = Packet(
        src_ip="192.168.1.100",
        dst_ip="10.0.0.10",
        protocol="tcp",
        port=80
    )
    matched_rule, time = engine.match_packet(packet)

    assert matched_rule is not None
    assert len(matched_rule.match_times) >= 1
    assert matched_rule.avg_match_time() > 0
    assert packet.match_time_us > 0


def test_average_match_time():
    rules = create_test_rules()
    engine = MatchingEngine(rules)

    for i in range(3):
        packet = Packet(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.10",
            protocol="tcp",
            port=80
        )
        engine.match_packet(packet)

    avg_time = engine.get_average_match_time()
    assert avg_time > 0
    assert engine.rules[0].hit_count == 3


def test_broad_subnet_matching():
    rules = [
        Rule({
            "id": "broad", "priority": 10,
            "src_ip": "0.0.0.0/0", "dst_ip": "0.0.0.0/0",
            "protocol": "tcp", "port": "any", "action": "allow"
        }),
    ]
    engine = MatchingEngine(rules)

    packet = Packet(
        src_ip="203.0.113.5",
        dst_ip="198.51.100.50",
        protocol="tcp",
        port=12345
    )
    matched_rule, time = engine.match_packet(packet)
    assert matched_rule is not None
    assert matched_rule.id == "broad"


def test_port_range_matching():
    rules = [
        Rule({
            "id": "range_test", "priority": 10,
            "src_ip": "192.168.1.0/24", "dst_ip": "10.0.0.0/8",
            "protocol": "tcp", "port": "8000-8010", "action": "allow"
        }),
    ]
    engine = MatchingEngine(rules)

    packet1 = Packet(
        src_ip="192.168.1.5", dst_ip="10.0.0.5",
        protocol="tcp", port=8005
    )
    matched1, _ = engine.match_packet(packet1)
    assert matched1.id == "range_test"

    packet2 = Packet(
        src_ip="192.168.1.5", dst_ip="10.0.0.5",
        protocol="tcp", port=8011
    )
    matched2, _ = engine.match_packet(packet2)
    assert matched2.id == "implicit_deny"


def test_multiple_packets_bulk():
    rules = create_test_rules()
    engine = MatchingEngine(rules)

    packets = [
        Packet(src_ip="192.168.1.1", dst_ip="10.0.0.1", protocol="tcp", port=80),
        Packet(src_ip="192.168.1.2", dst_ip="10.0.0.2", protocol="tcp", port=80),
        Packet(src_ip="10.0.0.10", dst_ip="1.2.3.4", protocol="icmp", port=0),
        Packet(src_ip="1.2.3.4", dst_ip="5.6.7.8", protocol="tcp", port=9999),
    ]

    results = engine.match_packets(packets)
    assert len(results) == 4
    assert results[0][0].id == "r1"
    assert results[1][0].id == "r1"
    assert results[2][0].id == "r3"
    assert results[3][0].id == "implicit_deny"

    assert engine.rules[0].hit_count == 2
    assert engine.rules[2].hit_count == 1
    assert engine.implicit_deny.hit_count == 1
