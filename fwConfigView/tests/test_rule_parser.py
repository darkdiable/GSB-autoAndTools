import os
import sys
import tempfile
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rule_parser import Rule, parse_csv, parse_json, load_rules, export_rules_to_json


def test_port_range_parsing_single():
    rule = Rule({
        "id": "test1", "priority": 1, "src_ip": "192.168.1.0/24",
        "dst_ip": "10.0.0.0/8", "protocol": "tcp", "port": "80", "action": "allow"
    })
    assert rule.port_start == 80
    assert rule.port_end == 80
    assert rule.port_any is False
    assert rule.matches_port(80) is True
    assert rule.matches_port(81) is False


def test_port_range_parsing_range():
    rule = Rule({
        "id": "test2", "priority": 1, "src_ip": "192.168.1.0/24",
        "dst_ip": "10.0.0.0/8", "protocol": "tcp", "port": "8080-8090", "action": "allow"
    })
    assert rule.port_start == 8080
    assert rule.port_end == 8090
    assert rule.matches_port(8080) is True
    assert rule.matches_port(8085) is True
    assert rule.matches_port(8090) is True
    assert rule.matches_port(8079) is False
    assert rule.matches_port(8091) is False


def test_port_range_parsing_any():
    rule = Rule({
        "id": "test3", "priority": 1, "src_ip": "192.168.1.0/24",
        "dst_ip": "10.0.0.0/8", "protocol": "tcp", "port": "any", "action": "allow"
    })
    assert rule.port_any is True
    assert rule.matches_port(1) is True
    assert rule.matches_port(65535) is True
    assert rule.matches_port(22) is True


def test_protocol_matching():
    rule = Rule({
        "id": "test4", "priority": 1, "src_ip": "192.168.1.0/24",
        "dst_ip": "10.0.0.0/8", "protocol": "tcp", "port": "80", "action": "allow"
    })
    assert rule.matches_protocol("tcp") is True
    assert rule.matches_protocol("TCP") is True
    assert rule.matches_protocol("udp") is False


def test_protocol_any():
    rule = Rule({
        "id": "test5", "priority": 1, "src_ip": "192.168.1.0/24",
        "dst_ip": "10.0.0.0/8", "protocol": "any", "port": "80", "action": "allow"
    })
    assert rule.matches_protocol("tcp") is True
    assert rule.matches_protocol("udp") is True
    assert rule.matches_protocol("icmp") is True


def test_priority_sorting():
    rules_data = [
        {"id": "r1", "priority": 30, "src_ip": "192.168.1.0/24", "dst_ip": "10.0.0.0/8",
         "protocol": "tcp", "port": "80", "action": "allow"},
        {"id": "r2", "priority": 10, "src_ip": "192.168.1.0/24", "dst_ip": "10.0.0.0/8",
         "protocol": "tcp", "port": "443", "action": "allow"},
        {"id": "r3", "priority": 20, "src_ip": "192.168.1.0/24", "dst_ip": "10.0.0.0/8",
         "protocol": "tcp", "port": "22", "action": "allow"},
    ]
    rules = [Rule(rd) for rd in rules_data]
    rules.sort(key=lambda r: r.priority)
    assert [r.id for r in rules] == ["r2", "r3", "r1"]
    assert [r.priority for r in rules] == [10, 20, 30]


def test_invalid_protocol():
    with pytest.raises(ValueError, match="Invalid protocol"):
        Rule({
            "id": "test6", "priority": 1, "src_ip": "192.168.1.0/24",
            "dst_ip": "10.0.0.0/8", "protocol": "invalid", "port": "80", "action": "allow"
        })


def test_invalid_action():
    with pytest.raises(ValueError, match="Invalid action"):
        Rule({
            "id": "test7", "priority": 1, "src_ip": "192.168.1.0/24",
            "dst_ip": "10.0.0.0/8", "protocol": "tcp", "port": "80", "action": "invalid"
        })


def test_invalid_ip():
    with pytest.raises(ValueError, match="Invalid src_ip"):
        Rule({
            "id": "test8", "priority": 1, "src_ip": "999.999.999.999",
            "dst_ip": "10.0.0.0/8", "protocol": "tcp", "port": "80", "action": "allow"
        })


def test_invalid_port_range():
    with pytest.raises(ValueError, match="Invalid port range"):
        Rule({
            "id": "test9", "priority": 1, "src_ip": "192.168.1.0/24",
            "dst_ip": "10.0.0.0/8", "protocol": "tcp", "port": "90-80", "action": "allow"
        })


def test_single_ip_parsing():
    rule = Rule({
        "id": "test10", "priority": 1, "src_ip": "192.168.1.100",
        "dst_ip": "10.0.0.5", "protocol": "tcp", "port": "22", "action": "allow"
    })
    assert rule.src_ip == "192.168.1.100"
    assert rule.dst_ip == "10.0.0.5"


def test_json_import_export_roundtrip():
    rules_data = [
        {"id": "r1", "priority": 10, "src_ip": "192.168.1.0/24", "dst_ip": "10.0.0.0/8",
         "protocol": "tcp", "port": "80", "action": "allow"},
        {"id": "r2", "priority": 20, "src_ip": "172.16.0.0/12", "dst_ip": "192.168.0.0/16",
         "protocol": "udp", "port": "53", "action": "deny"},
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(rules_data, f)
        temp_path = f.name

    try:
        rules = parse_json(temp_path)
        assert len(rules) == 2
        assert rules[0].id == "r1"
        assert rules[1].id == "r2"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
            export_path = f2.name

        try:
            export_rules_to_json(rules, export_path)
            with open(export_path, 'r') as f3:
                exported = json.load(f3)
            assert len(exported) == 2
            assert exported[0]["id"] == "r1"
            assert exported[0]["priority"] == 10
            assert exported[1]["port"] == "53"
        finally:
            os.unlink(export_path)
    finally:
        os.unlink(temp_path)


def test_csv_parsing():
    csv_content = """id,priority,src_ip,dst_ip,protocol,port,action
r1,10,192.168.1.0/24,10.0.0.0/8,tcp,80,allow
r2,20,172.16.0.0/12,192.168.0.0/16,udp,53,deny
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        rules = parse_csv(temp_path)
        assert len(rules) == 2
        assert rules[0].id == "r1"
        assert rules[0].priority == 10
        assert rules[1].protocol == "udp"
        assert rules[1].action == "deny"
    finally:
        os.unlink(temp_path)


def test_load_rules_detects_format():
    json_data = [{"id": "r1", "priority": 1, "src_ip": "192.168.1.0/24",
                   "dst_ip": "10.0.0.0/8", "protocol": "tcp", "port": "80", "action": "allow"}]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(json_data, f)
        json_path = f.name

    csv_content = """id,priority,src_ip,dst_ip,protocol,port,action
r1,1,192.168.1.0/24,10.0.0.0/8,tcp,80,allow
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        rules_json = load_rules(json_path)
        assert len(rules_json) == 1
        rules_csv = load_rules(csv_path)
        assert len(rules_csv) == 1
    finally:
        os.unlink(json_path)
        os.unlink(csv_path)


def test_to_dict():
    rule = Rule({
        "id": "r1", "priority": 10, "src_ip": "192.168.1.0/24",
        "dst_ip": "10.0.0.0/8", "protocol": "tcp", "port": "8080-8090", "action": "allow"
    })
    d = rule.to_dict()
    assert d["id"] == "r1"
    assert d["priority"] == 10
    assert d["port"] == "8080-8090"
    assert "hit_count" not in d
