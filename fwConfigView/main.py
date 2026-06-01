import argparse
import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.rule_parser import load_rules, export_rules_to_json, Rule
from src.matching_engine import MatchingEngine
from src.traffic_generator import TrafficGenerator
from src.report_generator import ReportGenerator


def run_benchmark():
    print("=" * 60)
    print("FIREWALL POLICY BENCHMARK MODE")
    print("=" * 60)

    generator = TrafficGenerator(seed=42)
    print("Generating 20000 random rules...")
    rule_dicts = generator.generate_random_rules(20000)
    rules = [Rule(rd) for rd in rule_dicts]
    rules.sort(key=lambda r: r.priority)

    print("Generating 10000 random packets...")
    packets = generator.generate_packets(count=10000)

    print("Initializing matching engine...")
    engine = MatchingEngine(rules)

    print("\nStarting benchmark...")
    start = time.perf_counter()
    engine.match_packets(packets)
    total_time = time.perf_counter() - start

    total_packets = len(packets)
    pps = total_packets / total_time if total_time > 0 else 0

    stats = engine.get_statistics()

    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Total Rules:        {stats['total_rules']}")
    print(f"Total Packets:      {total_packets}")
    print(f"Total Match Time:   {total_time:.4f} seconds")
    print(f"Packets Per Second: {pps:.2f}")
    print(f"Avg Match Time:     {stats['average_match_time_us']:.4f} μs")
    print(f"Allowed:            {stats['allow_count']}")
    print(f"Denied:             {stats['deny_count']}")
    print(f"Implicit Deny:      {stats['implicit_deny_hits']}")
    print("=" * 60)


def run_simulation(args):
    print("=" * 60)
    print("FIREWALL POLICY CONFIGURATION SIMULATOR")
    print("=" * 60)

    print(f"\nLoading rules from: {args.rules}")
    rules = load_rules(args.rules)
    print(f"Loaded {len(rules)} rules")

    if args.export_json:
        export_path = args.export_json
        print(f"\nExporting rules to: {export_path}")
        export_rules_to_json(rules, export_path)
        print("Export complete")

    print(f"\nGenerating {args.packets} random packets...")
    generator = TrafficGenerator()
    packets = generator.generate_packets(count=args.packets)

    print("Initializing matching engine...")
    engine = MatchingEngine(rules)

    print("Matching packets against rules...")
    engine.match_packets(packets)

    stats = engine.get_statistics()
    print("\n" + "=" * 60)
    print("SIMULATION RESULTS")
    print("=" * 60)
    print(f"Total Rules:        {stats['total_rules']}")
    print(f"Total Packets:      {args.packets}")
    print(f"Avg Match Time:     {stats['average_match_time_us']:.4f} μs")
    print(f"Allowed:            {stats['allow_count']}")
    print(f"Denied:             {stats['deny_count']}")
    print(f"Implicit Deny:      {stats['implicit_deny_hits']}")
    print("=" * 60)

    print(f"\nGenerating HTML report to: {args.output}")
    report_gen = ReportGenerator(engine, args.output)
    report_path = report_gen.generate_report()
    print(f"Report generated: {report_path}")

    print("\nDone!")


def main():
    parser = argparse.ArgumentParser(description="Firewall Policy Configuration Simulator")
    parser.add_argument("--rules", type=str, help="Path to rules file (CSV or JSON)")
    parser.add_argument("--packets", type=int, default=500, help="Number of packets to generate (default: 500)")
    parser.add_argument("--output", type=str, default="output", help="Output directory for reports")
    parser.add_argument("--export-json", type=str, help="Export rules to JSON file")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark mode with 20000 rules and 10000 packets")

    args = parser.parse_args()

    if args.benchmark:
        run_benchmark()
    else:
        if not args.rules:
            parser.error("--rules is required unless --benchmark is specified")
        run_simulation(args)


if __name__ == "__main__":
    main()
