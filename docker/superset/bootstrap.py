"""Create the ClickHouse connection, datasets, and the tariff dashboard.

The dashboard has the two product modes: a network table for scanning lanes,
and a monthly corridor chart for one lane. Filters default to Москва → Тула,
тент, FTL, and apply only to the route card.
"""

import json
import os

from superset.app import create_app

CLICKHOUSE_URI = "clickhousedb://{user}:{password}@clickhouse:8123/mart".format(
    user=os.environ.get("CLICKHOUSE_USER", "default"),
    password=os.environ.get("CLICKHOUSE_PASSWORD", "clickhouse"),
)


def main() -> None:
    application = create_app()
    with application.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = _database(db, Database)
        route = _dataset(db, SqlaTable, database, "mart_route_card")
        _dataset(db, SqlaTable, database, "ml_price_predictions")
        network = _network_chart(db, Slice, route)
        card = _card_chart(db, Slice, route)
        _dashboard(db, Dashboard, network, card)
        db.session.commit()


def _database(db, database_cls):
    found = db.session.query(database_cls).filter_by(database_name="ClickHouse mart").one_or_none()
    if found is not None:
        return found
    created = database_cls(
        database_name="ClickHouse mart",
        sqlalchemy_uri=CLICKHOUSE_URI,
        expose_in_sqllab=True,
        allow_run_async=False,
    )
    db.session.add(created)
    db.session.commit()
    return created


def _dataset(db, table_cls, database, table_name):
    found = (
        db.session.query(table_cls)
        .filter_by(table_name=table_name, database_id=database.id)
        .one_or_none()
    )
    if found is not None:
        return found
    created = table_cls(table_name=table_name, schema="mart", database=database)
    db.session.add(created)
    db.session.flush()
    created.fetch_metadata()
    db.session.commit()
    return created


def _network_chart(db, slice_cls, dataset):
    params = {
        "datasource": f"{dataset.id}__table",
        "viz_type": "table",
        "query_mode": "raw",
        "all_columns": [
            "price_month",
            "loading_city_name",
            "unloading_city_name",
            "body_group",
            "weight_category",
            "p25_trip",
            "median_trip",
            "p75_trip",
            "p25_km",
            "median_km",
            "p75_km",
            "trips_count",
            "carriers_count",
            "reliability_level",
            "mom_pct",
            "yoy_pct",
        ],
        "row_limit": 500,
        "order_desc": True,
    }
    return _upsert_chart(
        db, slice_cls, dataset, "Сеть маршрутов", "table", params, "Коридор ставок"
    )


def _card_chart(db, slice_cls, dataset):
    params = {
        "datasource": f"{dataset.id}__table",
        "viz_type": "echarts_timeseries_line",
        "x_axis": "price_month",
        "time_grain_sqla": "P1M",
        "metrics": [
            _avg_metric("p25_trip", "P25, руб/рейс"),
            _avg_metric("median_trip", "Медиана, руб/рейс"),
            _avg_metric("p75_trip", "P75, руб/рейс"),
        ],
        "groupby": [],
        "row_limit": 10000,
        "adhoc_filters": [],
    }
    return _upsert_chart(
        db, slice_cls, dataset, "Карточка маршрута", "echarts_timeseries_line", params
    )


def _avg_metric(column: str, label: str) -> dict:
    return {
        "expressionType": "SIMPLE",
        "column": {"column_name": column},
        "aggregate": "AVG",
        "label": label,
    }


def _upsert_chart(db, slice_cls, dataset, name, viz_type, params, legacy_name=None):
    names = [name] if legacy_name is None else [name, legacy_name]
    found = (
        db.session.query(slice_cls)
        .filter(slice_cls.slice_name.in_(names))
        .order_by(slice_cls.id)
        .first()
    )
    if found is None:
        found = slice_cls(slice_name=name)
        db.session.add(found)
    found.slice_name = name
    found.viz_type = viz_type
    found.datasource_id = dataset.id
    found.datasource_type = "table"
    found.params = json.dumps(params)
    db.session.commit()
    return found


def _layout(network, card):
    # A chart is visible only when a ROW owns it. A chart placed directly on the grid
    # is dropped, and Superset then persists an empty layout.
    return {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {
            "type": "GRID",
            "id": "GRID_ID",
            "children": ["ROW-NETWORK", "ROW-CARD"],
            "parents": ["ROOT_ID"],
        },
        "HEADER_ID": {"id": "HEADER_ID", "type": "HEADER", "meta": {"text": "Ставки"}},
        "ROW-NETWORK": _row("ROW-NETWORK", ["CHART-NETWORK"]),
        "CHART-NETWORK": _chart_node("CHART-NETWORK", "ROW-NETWORK", network, height=50),
        "ROW-CARD": _row("ROW-CARD", ["CHART-CARD"]),
        "CHART-CARD": _chart_node("CHART-CARD", "ROW-CARD", card, height=40),
    }


def _row(row_id, children):
    return {
        "type": "ROW",
        "id": row_id,
        "children": children,
        "parents": ["ROOT_ID", "GRID_ID"],
        "meta": {"background": "BACKGROUND_TRANSPARENT"},
    }


def _chart_node(node_id, row_id, chart, *, height):
    return {
        "type": "CHART",
        "id": node_id,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", row_id],
        "meta": {
            "chartId": chart.id,
            "height": height,
            "sliceName": chart.slice_name,
            "width": 12,
        },
    }


def _select_filter(filter_id, name, column, dataset_id, chart_id, default, excluded):
    return {
        "id": filter_id,
        "name": name,
        "filterType": "filter_select",
        "targets": [{"datasetId": dataset_id, "column": {"name": column}}],
        "defaultDataMask": {
            "extraFormData": {"filters": [{"col": column, "op": "IN", "val": [default]}]},
            "filterState": {"value": [default]},
            "ownState": {},
        },
        "controlValues": {
            "enableEmptyFilter": False,
            "defaultToFirstItem": False,
            "multiSelect": False,
            "searchAllOptions": True,
            "inverseSelection": False,
        },
        "cascadeParentIds": [],
        "scope": {"rootPath": ["ROOT_ID"], "excluded": [excluded]},
        "chartsInScope": [chart_id],
        "tabsInScope": [],
        "type": "NATIVE_FILTER",
    }


def _dashboard(db, dashboard_cls, network, card):
    dashboard = db.session.query(dashboard_cls).filter_by(dashboard_title="Ставки").one_or_none()
    if dashboard is None:
        dashboard = dashboard_cls(dashboard_title="Ставки", slug="tariffs")
        db.session.add(dashboard)
    dashboard.published = True
    dashboard.slug = "tariffs"
    dashboard.position_json = json.dumps(_layout(network, card))
    dashboard.json_metadata = json.dumps(
        {
            "chart_configuration": {
                str(chart.id): {
                    "id": chart.id,
                    "crossFilters": {"scope": "global", "chartsInScope": []},
                }
                for chart in (network, card)
            },
            "global_chart_configuration": {
                "scope": {"rootPath": ["ROOT_ID"], "excluded": []},
                "chartsInScope": [network.id, card.id],
            },
            "native_filter_configuration": [
                _select_filter(
                    "NATIVE_FILTER-ORIGIN",
                    "Город отправления",
                    "loading_city_name",
                    network.datasource_id,
                    card.id,
                    "Москва",
                    network.id,
                ),
                _select_filter(
                    "NATIVE_FILTER-DESTINATION",
                    "Город назначения",
                    "unloading_city_name",
                    network.datasource_id,
                    card.id,
                    "Тула",
                    network.id,
                ),
                _select_filter(
                    "NATIVE_FILTER-BODY",
                    "Группа кузова",
                    "body_group",
                    network.datasource_id,
                    card.id,
                    "Тент",
                    network.id,
                ),
                _select_filter(
                    "NATIVE_FILTER-WEIGHT",
                    "Весовая категория",
                    "weight_category",
                    network.datasource_id,
                    card.id,
                    "FTL",
                    network.id,
                ),
            ],
            "color_scheme": "",
            "refresh_frequency": 0,
            "expanded_slices": {},
            "label_colors": {},
            "timed_refresh_immune_slices": [],
            "cross_filters_enabled": False,
        }
    )
    dashboard.slices = [network, card]
    db.session.commit()
    return dashboard


if __name__ == "__main__":
    main()
