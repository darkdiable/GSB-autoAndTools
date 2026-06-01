import os
from typing import List, Dict
from .rule_parser import Rule
from .matching_engine import MatchingEngine
from .visualization import Visualizer


class ReportGenerator:
    def __init__(self, engine: MatchingEngine, output_dir: str):
        self.engine = engine
        self.output_dir = output_dir
        self.visualizer = Visualizer(engine)
        os.makedirs(output_dir, exist_ok=True)

    def _generate_rules_table(self, rules: List[Rule]) -> str:
        rows = []
        for rule in rules:
            action_class = "allow" if rule.action == "allow" else "deny"
            avg_time = f"{rule.avg_match_time():.4f}" if rule.match_times else "N/A"
            is_implicit = "implicit-row" if rule.id == "implicit_deny" else ""
            rows.append(f"""
                <tr class="{is_implicit}">
                    <td>{rule.id}</td>
                    <td>{rule.priority}</td>
                    <td>{rule.src_ip}</td>
                    <td>{rule.dst_ip}</td>
                    <td>{rule.protocol}</td>
                    <td>{rule.port}</td>
                    <td class="action-{action_class}">{rule.action}</td>
                    <td class="hit-count">{rule.hit_count}</td>
                    <td>{avg_time} μs</td>
                </tr>
            """)
        return "\n".join(rows)

    def _generate_unmatched_rules(self, rules: List[Rule]) -> str:
        unmatched = [r for r in rules if r.hit_count == 0 and r.id != "implicit_deny"]
        if not unmatched:
            return "<p>No unmatched rules.</p>"

        items = []
        for rule in unmatched:
            items.append(f"""
                <li>
                    <strong>{rule.id}</strong> (Priority: {rule.priority}) - 
                    {rule.src_ip} → {rule.dst_ip}, {rule.protocol}/{rule.port}, {rule.action}
                </li>
            """)
        items_html = "\n".join(items)
        return f"""
            <details class="unmatched-details">
                <summary>Unmatched Rules ({len(unmatched)})</summary>
                <ul class="unmatched-list">
                    {items_html}
                </ul>
            </details>
        """

    def generate_report(self) -> str:
        stats = self.engine.get_statistics()
        charts = self.visualizer.generate_all_charts(stats)
        all_rules = self.engine.get_all_rules()
        explicit_rules = [r for r in all_rules if r.id != "implicit_deny"]
        implicit_rule = self.engine.implicit_deny

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Firewall Policy Simulation Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #333; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ text-align: center; color: #2c3e50; margin-bottom: 30px; font-size: 28px; }}
        h2 {{ color: #34495e; margin: 30px 0 15px; font-size: 22px; border-bottom: 2px solid #3498db; padding-bottom: 8px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
        .stat-card .label {{ font-size: 14px; color: #7f8c8d; margin-bottom: 8px; }}
        .stat-card .value {{ font-size: 28px; font-weight: bold; color: #2c3e50; }}
        .stat-card.allow .value {{ color: #27ae60; }}
        .stat-card.deny .value {{ color: #e74c3c; }}
        .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .chart-container.full {{ grid-column: 1 / -1; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ecf0f1; }}
        th {{ background: #34495e; color: white; font-weight: 600; }}
        tr:hover {{ background: #f8f9fa; }}
        tr.implicit-row {{ background: #fff3cd; }}
        tr.implicit-row:hover {{ background: #ffeeba; }}
        .action-allow {{ color: #27ae60; font-weight: 600; }}
        .action-deny {{ color: #e74c3c; font-weight: 600; }}
        .hit-count {{ font-weight: 600; }}
        .unmatched-details {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 20px; }}
        .unmatched-details summary {{ cursor: pointer; font-weight: 600; color: #34495e; padding: 5px 0; }}
        .unmatched-list {{ margin: 15px 0 0 20px; }}
        .unmatched-list li {{ padding: 8px 0; border-bottom: 1px solid #ecf0f1; }}
        .unmatched-list li:last-child {{ border-bottom: none; }}
        @media (max-width: 1000px) {{
            .charts-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Firewall Policy Configuration Simulation Report</h1>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Total Rules</div>
                <div class="value">{stats['total_rules']}</div>
            </div>
            <div class="stat-card allow">
                <div class="label">Allowed Packets</div>
                <div class="value">{stats['allow_count']}</div>
            </div>
            <div class="stat-card deny">
                <div class="label">Denied Packets</div>
                <div class="value">{stats['deny_count']}</div>
            </div>
            <div class="stat-card deny">
                <div class="label">Implicit Deny Hits</div>
                <div class="value">{stats['implicit_deny_hits']}</div>
            </div>
            <div class="stat-card">
                <div class="label">Avg Match Time</div>
                <div class="value">{stats['average_match_time_us']:.2f} μs</div>
            </div>
        </div>

        <h2>Visualization</h2>
        <div class="charts-grid">
            <div class="chart-container">
                {charts['pie_chart']}
            </div>
            <div class="chart-container">
                {charts['bar_chart']}
            </div>
            <div class="chart-container full">
                {charts['scatter_chart']}
            </div>
            <div class="chart-container full">
                {charts['heatmap']}
            </div>
        </div>

        <h2>Rule Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Rule ID</th>
                    <th>Priority</th>
                    <th>Source IP</th>
                    <th>Destination IP</th>
                    <th>Protocol</th>
                    <th>Port</th>
                    <th>Action</th>
                    <th>Hit Count</th>
                    <th>Avg Match Time</th>
                </tr>
            </thead>
            <tbody>
                {self._generate_rules_table(explicit_rules)}
                {self._generate_rules_table([implicit_rule])}
            </tbody>
        </table>

        {self._generate_unmatched_rules(all_rules)}
    </div>
</body>
</html>
        """

        output_path = os.path.join(self.output_dir, "report.html")
        with open(output_path, "w") as f:
            f.write(html)

        return output_path
