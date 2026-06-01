import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict
from .rule_parser import Rule
from .matching_engine import MatchingEngine


class Visualizer:
    def __init__(self, engine: MatchingEngine):
        self.engine = engine
        self.all_rules = engine.get_all_rules()

    def create_action_pie_chart(self, stats: Dict) -> str:
        labels = ["Allow", "Deny"]
        values = [stats["allow_count"], stats["deny_count"]]
        colors = ["#2ecc71", "#e74c3c"]

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4,
                    marker=dict(colors=colors),
                    textinfo="label+percent+value",
                )
            ]
        )
        fig.update_layout(
            title="Allow vs Deny Distribution",
            title_x=0.5,
        )
        return fig.to_html(full_html=False, include_plotlyjs=False)

    def create_top_rules_bar_chart(self, top_n: int = 10) -> str:
        sorted_rules = sorted(
            [r for r in self.all_rules if r.id != "implicit_deny"],
            key=lambda r: r.hit_count,
            reverse=True,
        )[:top_n]

        rule_ids = [r.id for r in sorted_rules]
        hit_counts = [r.hit_count for r in sorted_rules]
        colors = ["#3498db" if r.action == "allow" else "#e74c3c" for r in sorted_rules]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=rule_ids,
                    y=hit_counts,
                    marker_color=colors,
                    text=hit_counts,
                    textposition="auto",
                )
            ]
        )
        fig.update_layout(
            title=f"Top {top_n} Rules by Hit Count",
            title_x=0.5,
            xaxis_title="Rule ID",
            yaxis_title="Hit Count",
            showlegend=False,
        )
        return fig.to_html(full_html=False, include_plotlyjs=False)

    def create_rule_efficiency_scatter(self) -> str:
        priorities = []
        avg_times = []
        hit_counts = []
        rule_ids = []
        colors = []

        for rule in self.all_rules:
            if rule.hit_count > 0:
                priorities.append(rule.priority)
                avg_times.append(rule.avg_match_time())
                hit_counts.append(max(rule.hit_count, 1) * 10)
                rule_ids.append(rule.id)
                colors.append("#3498db" if rule.action == "allow" else "#e74c3c")

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=priorities,
                    y=avg_times,
                    mode="markers",
                    marker=dict(size=hit_counts, color=colors, opacity=0.7),
                    text=rule_ids,
                    hovertemplate=(
                        "Rule: %{text}<br>"
                        "Priority: %{x}<br>"
                        "Avg Time: %{y:.2f} μs<br>"
                        "<extra></extra>"
                    ),
                )
            ]
        )
        fig.update_layout(
            title="Rule Efficiency: Priority vs Match Time",
            title_x=0.5,
            xaxis_title="Priority (lower = checked earlier)",
            yaxis_title="Average Match Time (μs)",
        )
        return fig.to_html(full_html=False, include_plotlyjs=False)

    def create_protocol_heatmap(self, stats: Dict) -> str:
        protocols = ["tcp", "udp", "icmp"]
        actions = ["allow", "deny"]

        z = []
        for proto in protocols:
            row = [stats["protocol_hits"][proto][action] for action in actions]
            z.append(row)

        fig = go.Figure(
            data=go.Heatmap(
                z=z,
                x=actions,
                y=protocols,
                text=[[str(v) for v in row] for row in z],
                texttemplate="%{text}",
                textfont={"size": 12},
                colorscale="Blues",
                hoverongaps=False,
            )
        )
        fig.update_layout(
            title="Protocol Hit Distribution by Action",
            title_x=0.5,
            xaxis_title="Action",
            yaxis_title="Protocol",
        )
        return fig.to_html(full_html=False, include_plotlyjs=False)

    def generate_all_charts(self, stats: Dict) -> Dict[str, str]:
        return {
            "pie_chart": self.create_action_pie_chart(stats),
            "bar_chart": self.create_top_rules_bar_chart(10),
            "scatter_chart": self.create_rule_efficiency_scatter(),
            "heatmap": self.create_protocol_heatmap(stats),
        }
