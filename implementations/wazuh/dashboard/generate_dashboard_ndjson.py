#!/usr/bin/env python3
"""
Generates implementations/wazuh/dashboard/saved-objects/pdp-dashboard-shell.ndjson
from implementations/wazuh/dashboard/DASHBOARD_SPEC.yml.

Produces classic (vislib/table) OpenSearch Dashboards / Kibana 7.x-compatible
saved objects: one index-pattern per DASHBOARD_SPEC.metadata.indices entry,
one visualization per DASHBOARD_SPEC.panels entry, and a dashboard tying them
together in a 2-column grid.

Panel `type` values supported: metric+distribution and bar -> histogram;
pie -> pie; table -> table; timeseries -> line (date_histogram + terms split).

Re-run this after editing DASHBOARD_SPEC.yml, then re-import with
release/runtime-validation/dashboard/validate_real_import.py against a real
target to confirm the aggregations still execute against the real field
mappings in implementations/wazuh/indexer/templates/.
"""
from pathlib import Path
import json
import yaml


def find_repo_root(start):
    p = Path(start).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "FRAMEWORK_MANIFEST.yml").exists():
            return candidate
    raise RuntimeError("Repository root not found")


ROOT = find_repo_root(Path(__file__).parent)
SPEC_PATH = ROOT / "implementations/wazuh/dashboard/DASHBOARD_SPEC.yml"
OUT_PATH = ROOT / "implementations/wazuh/dashboard/saved-objects/pdp-dashboard-shell.ndjson"


def index_pattern_id(index_glob):
    # "pdp-evidence-*" -> "pdp-evidence-index-pattern"
    return index_glob.rstrip("*").rstrip("-") + "-index-pattern"


def search_source(query=None):
    return json.dumps({
        "query": {"query": query or "", "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    })


def viz_obj(obj_id, title, index_glob, vis_state, description="", query=None):
    return {
        "type": "visualization",
        "id": obj_id,
        "attributes": {
            "title": title,
            "visState": json.dumps(vis_state),
            "uiStateJSON": "{}",
            "description": description,
            "version": 1,
            "kibanaSavedObjectMeta": {"searchSourceJSON": search_source(query)},
        },
        "references": [
            {
                "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                "type": "index-pattern",
                "id": index_pattern_id(index_glob),
            }
        ],
    }


def metric_count():
    return {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}}


def terms_agg(agg_id, field, schema, size=10):
    return {
        "id": agg_id,
        "enabled": True,
        "type": "terms",
        "schema": schema,
        "params": {
            "field": field,
            "orderBy": "1",
            "order": "desc",
            "size": size,
            "otherBucket": False,
            "otherBucketLabel": "Other",
            "missingBucket": False,
            "missingBucketLabel": "Missing",
        },
    }


def _series_vis(title, chart_type, field):
    return {
        "title": title,
        "type": chart_type,
        "params": {
            "type": chart_type,
            "grid": {"categoryLines": False},
            "categoryAxes": [{
                "id": "CategoryAxis-1", "type": "category", "position": "bottom", "show": True,
                "style": {}, "scale": {"type": "linear"},
                "labels": {"show": True, "filter": True, "truncate": 100}, "title": {},
            }],
            "valueAxes": [{
                "id": "ValueAxis-1", "name": "LeftAxis-1", "type": "value", "position": "left",
                "show": True, "style": {}, "scale": {"type": "linear", "mode": "normal"},
                "labels": {"show": True, "rotate": 0, "filter": False, "truncate": 100},
                "title": {"text": "Count"},
            }],
            "seriesParams": [{
                "show": True, "type": chart_type, "mode": "stacked" if chart_type == "histogram" else "normal",
                "data": {"label": "Count", "id": "1"}, "valueAxis": "ValueAxis-1",
                "drawLinesBetweenPoints": True, "showCircles": True,
            }],
            "addTooltip": True, "addLegend": True, "legendPosition": "right",
            "times": [], "addTimeMarker": False, "labels": {"show": False},
            "thresholdLine": {"show": False, "value": 10, "width": 1, "style": "full", "color": "#E7664C"},
        },
        "aggs": [metric_count(), terms_agg("2", field, "segment")],
    }


def bar_vis(title, field):
    return _series_vis(title, "histogram", field)


def pie_vis(title, field):
    return {
        "title": title,
        "type": "pie",
        "params": {
            "type": "pie", "addTooltip": True, "addLegend": True, "legendPosition": "right",
            "isDonut": True, "labels": {"show": False, "values": True, "last_level": True, "truncate": 100},
        },
        "aggs": [metric_count(), terms_agg("2", field, "segment")],
    }


def table_vis(title, fields, metric_agg=None, size=20):
    aggs = [metric_agg or metric_count()]
    for i, f in enumerate(fields, start=2):
        aggs.append(terms_agg(str(i), f, "bucket", size=size))
    return {
        "title": title,
        "type": "table",
        "params": {
            "perPage": 10, "showPartialRows": False, "showMetricsAtAllLevels": False,
            "sort": {"columnIndex": None, "direction": None}, "showTotal": False, "totalFunc": "sum",
        },
        "aggs": aggs,
    }


def line_vis_over_time(title, time_field, split_field):
    return {
        "title": title,
        "type": "line",
        "params": {
            "type": "line",
            "grid": {"categoryLines": False},
            "categoryAxes": [{
                "id": "CategoryAxis-1", "type": "category", "position": "bottom", "show": True,
                "style": {}, "scale": {"type": "linear"},
                "labels": {"show": True, "filter": True, "truncate": 100}, "title": {},
            }],
            "valueAxes": [{
                "id": "ValueAxis-1", "name": "LeftAxis-1", "type": "value", "position": "left",
                "show": True, "style": {}, "scale": {"type": "linear", "mode": "normal"},
                "labels": {"show": True, "rotate": 0, "filter": False, "truncate": 100},
                "title": {"text": "Count"},
            }],
            "seriesParams": [{
                "show": True, "type": "line", "mode": "normal",
                "data": {"label": "Count", "id": "1"}, "valueAxis": "ValueAxis-1",
                "drawLinesBetweenPoints": True, "showCircles": True,
            }],
            "addTooltip": True, "addLegend": True, "legendPosition": "right",
            "times": [], "addTimeMarker": False,
        },
        "aggs": [
            metric_count(),
            {
                "id": "2", "enabled": True, "type": "date_histogram", "schema": "segment",
                "params": {
                    "field": time_field, "timeRange": {"from": "now-90d", "to": "now"},
                    "useNormalizedOpenSearchInterval": True, "interval": "auto",
                    "drop_partials": False, "min_doc_count": 1, "extended_bounds": {},
                },
            },
            terms_agg("3", split_field, "group", size=5),
        ],
    }


# A field that is a metric (numeric aggregate) rather than a bucket, keyed by
# panel id -> field name. Everything else in `buckets` is treated as a terms
# bucket. This keeps the spec itself free of Kibana-specific annotations.
METRIC_OVERRIDES = {
    "PDP-DASH-005": "coverage.coverage_percent",
}


def build_panel_viz(panel):
    pid = panel["id"]
    title = f"{pid}: {panel['title']}"
    ptype = panel["type"]
    index = panel["index"]
    buckets = list(panel.get("buckets", []))
    query = panel.get("filter")

    metric_field = METRIC_OVERRIDES.get(pid)
    if metric_field and metric_field in buckets:
        buckets.remove(metric_field)

    if ptype in ("metric+distribution", "bar"):
        vis_state = bar_vis(title, buckets[0])
    elif ptype == "pie":
        vis_state = pie_vis(title, buckets[0])
    elif ptype == "table":
        metric_agg = None
        if metric_field:
            metric_agg = {"id": "1", "enabled": True, "type": "avg", "schema": "metric",
                           "params": {"field": metric_field}}
        vis_state = table_vis(title, buckets, metric_agg=metric_agg)
    elif ptype == "timeseries":
        vis_state = line_vis_over_time(title, panel.get("time_field", "@timestamp"), buckets[0])
    else:
        raise ValueError(f"Unsupported panel type {ptype!r} for {pid}")

    description = panel.get("notes", "")
    return viz_obj(f"{pid.lower()}-viz", title, index, vis_state, description=description, query=query)


def main():
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    indices = spec["metadata"]["indices"]
    panels_spec = spec["panels"]

    index_patterns = [
        {
            "type": "index-pattern",
            "id": index_pattern_id(ix),
            "attributes": {"title": ix, "timeFieldName": "@timestamp"},
            "references": [],
        }
        for ix in indices
    ]

    viz_objects = [build_panel_viz(p) for p in panels_spec]

    panels = []
    refs = []
    w, h = 24, 15
    for i, viz in enumerate(viz_objects):
        row, col = divmod(i, 2)
        panel_index = str(i + 1)
        ref_name = f"panel_{panel_index}"
        panels.append({
            "version": "7.9.3",
            "type": "visualization",
            "gridData": {"x": col * w, "y": row * h, "w": w, "h": h, "i": panel_index},
            "panelIndex": panel_index,
            "embeddableConfig": {},
            "panelRefName": ref_name,
        })
        refs.append({"name": ref_name, "type": "visualization", "id": viz["id"]})

    dashboard = {
        "type": "dashboard",
        "id": "pdp-continuous-control-dashboard",
        "attributes": {
            "title": spec["metadata"]["title"],
            "description": f"{spec['metadata']['principle']}",
            "hits": 0,
            "panelsJSON": json.dumps(panels),
            "optionsJSON": json.dumps({"useMargins": True, "hidePanelTitles": False}),
            "version": 1,
            "timeRestore": False,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({"query": {"query": "", "language": "kuery"}, "filter": []})
            },
        },
        "references": refs,
    }

    all_objects = index_patterns + viz_objects + [dashboard]
    OUT_PATH.write_text("\n".join(json.dumps(o) for o in all_objects) + "\n", encoding="utf-8")
    print(f"Wrote {len(all_objects)} saved objects to {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
