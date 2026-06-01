# Firewall Policy Configuration Simulator

A Python-based firewall policy simulator with visualization capabilities. It allows you to test firewall rule sets against simulated network traffic and generate detailed HTML reports with interactive charts.

## Features

- **Rule File Support**: CSV and JSON formats with fields: id, priority, src_ip, dst_ip, protocol, port, action
- **CIDR Support**: Both src_ip and dst_ip support CIDR notation (e.g., 192.168.1.0/24) and single IPs
- **Port Matching**: Supports single ports (80), ranges (8080-8090), and "any"
- **Protocol Support**: tcp, udp, icmp
- **Priority Matching**: Rules are matched in ascending priority order
- **Implicit Deny**: Default implicit deny rule that catches unmatched packets (counted separately)
- **Traffic Generator**: Generates random packets with configurable protocol, port range, and IP subnet
- **Performance Tracking**: Records match time per rule in microseconds, calculates averages
- **Visualization**:
  - Pie chart showing allow/deny distribution
  - Bar chart showing top 10 rules by hit count
  - Scatter plot showing rule efficiency (priority vs match time)
  - Heatmap showing protocol hit distribution by action
- **HTML Report**: Complete report with all charts, rule details table, and unmatched rules list
- **Benchmark Mode**: Performance testing with 20000 rules and 10000 packets
- **Unit Tests**: Comprehensive test coverage using pytest

## Installation

```bash
cd fwConfigView
pip install -r requirements.txt
```

## Rule File Format

### CSV Format
```csv
id,priority,src_ip,dst_ip,protocol,port,action
rule_001,10,192.168.1.0/24,10.0.0.0/8,tcp,80,allow
rule_002,20,192.168.1.0/24,10.0.0.0/8,tcp,443,allow
```

### JSON Format
```json
[
  {
    "id": "rule_001",
    "priority": 10,
    "src_ip": "192.168.1.0/24",
    "dst_ip": "10.0.0.0/8",
    "protocol": "tcp",
    "port": "80",
    "action": "allow"
  }
]
```

### Field Descriptions
- **id**: Unique rule identifier
- **priority**: Integer priority (lower = checked earlier)
- **src_ip**: Source IP (CIDR or single IP, e.g., "192.168.1.0/24" or "192.168.1.100")
- **dst_ip**: Destination IP (CIDR or single IP)
- **protocol**: "tcp", "udp", or "icmp"
- **port**: Single port ("80"), range ("8080-8090"), or "any"
- **action**: "allow" or "deny"

## Usage Examples

### Basic Simulation with CSV Rules
```bash
python main.py --rules sample_rules.csv --packets 500 --output output
```

### Basic Simulation with JSON Rules
```bash
python main.py --rules sample_rules.json --packets 1000 --output output_json
```

### Export Rules to JSON
```bash
python main.py --rules sample_rules.csv --export-json output/exported.json --output output
```

### Benchmark Mode
```bash
python main.py --benchmark
```

### Show Help
```bash
python main.py --help
```

## Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--rules` | Path to rules file (CSV or JSON) | Required (unless --benchmark) |
| `--packets` | Number of packets to generate | 500 |
| `--output` | Output directory for reports | output |
| `--export-json` | Path to export rules as JSON | None |
| `--benchmark` | Run benchmark mode | False |

## Running Tests

```bash
cd fwConfigView
pytest tests/ -v
```

## Project Structure

```
fwConfigView/
├── main.py                    # Main entry point
├── requirements.txt           # Dependencies
├── README.md                  # This file
├── sample_rules.csv           # Sample rules in CSV format
├── sample_rules.json          # Sample rules in JSON format
├── src/
│   ├── __init__.py
│   ├── rule_parser.py         # Rule parsing and validation
│   ├── matching_engine.py     # Packet matching with performance tracking
│   ├── traffic_generator.py   # Random packet generation
│   ├── visualization.py       # Chart generation with Plotly
│   └── report_generator.py    # HTML report generation
├── tests/
│   ├── __init__.py
│   ├── test_rule_parser.py    # Tests for rule parsing
│   └── test_matching_engine.py # Tests for matching engine
└── output/                    # Generated reports
```

## Output

The simulation generates:
- `output/report.html` - Interactive HTML report with all visualizations
- Optional JSON export if `--export-json` is specified

## Benchmark Output

Benchmark mode outputs:
- Total number of rules (20000)
- Total number of packets (10000)
- Total matching time (seconds)
- Packets per second (PPS)
- Average match time per rule (microseconds)
- Allow/deny counts
