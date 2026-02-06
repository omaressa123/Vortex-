import json

# Dashboard Template DSL:
# A design contract across Data, KPIs, Charts, Layout, Theme, Rules.

TEMPLATES = {
    # Image -> DSL Template mapping
    "1.jpeg": {
        "template_id": "executive_overview",
        "id": "1",
        "name": "Executive Sales Overview",
        "category": "business",
        "layout": {
            "type": "grid",
            "columns": 12,
            "row_height": 120,
            "gap": 16
        },
        "components": [
            {"id": "kpi_1", "type": "kpi", "label": "Primary Metric", "span": 3, "position": "row_1"},
            {"id": "kpi_2", "type": "kpi", "label": "Secondary Metric", "span": 3, "position": "row_1"},
            {"id": "kpi_3", "type": "kpi", "label": "Efficiency Metric", "span": 3, "position": "row_1"},
            {"id": "kpi_4", "type": "kpi", "label": "Auxiliary Metric", "span": 3, "position": "row_1"},
            {"id": "chart_main", "type": "line_chart", "label": "Trend Over Time", "span": 12, "position": "row_2"},
            {"id": "chart_secondary", "type": "bar_chart", "label": "Categorical Breakdown", "span": 12, "position": "row_3"}
        ],
        "theme": {
            "mode": "dark",
            "primary": "#6366f1",
            "accent": "#22d3ee",
            "background": "#0f172a",
            "font": "Inter"
        },
        "rules": {
            "kpi_position": "top",
            "max_charts_per_view": 5,
            "time_series_priority": "high"
        }
    },
    "default": {
        "template_id": "general_analytics",
        "id": "default",
        "name": "General Analytics",
        "category": "generic",
        "layout": {
            "type": "grid",
            "columns": 12,
            "row_height": 120,
            "gap": 16
        },
        "components": [
            {"id": "kpi_1", "type": "kpi", "label": "Key Metric 1", "span": 3, "position": "row_1"},
            {"id": "kpi_2", "type": "kpi", "label": "Key Metric 2", "span": 3, "position": "row_1"},
            {"id": "kpi_3", "type": "kpi", "label": "Key Metric 3", "span": 3, "position": "row_1"},
            {"id": "chart_main", "type": "line_chart", "label": "Trend", "span": 12, "position": "row_2"},
            {"id": "chart_secondary", "type": "bar_chart", "label": "Distribution", "span": 12, "position": "row_3"}
        ],
        "theme": {
            "mode": "dark",
            "primary": "#6366f1",
            "accent": "#22d3ee",
            "background": "#0f172a",
            "font": "Inter"
        },
        "rules": {
            "kpi_position": "top",
            "max_charts_per_view": 5,
            "time_series_priority": "medium"
        }
    }
}

def get_template_spec(filename):
    return TEMPLATES.get(filename, TEMPLATES["default"])
