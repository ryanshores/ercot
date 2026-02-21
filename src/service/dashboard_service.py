from collections import defaultdict
from datetime import datetime, timedelta, UTC

from sqlalchemy.orm import Session

from src.models.energy import GenInstant, energy_sources
from src.service.db.gen_instant import get_by_dates


class DashboardService:
    # Map units to days for conversion
    UNIT_MAP = {"D": 1, "W": 7, "M": 30, "Y": 365}

    CUSTOM_ORDER = [
        "nuclear",
        "coal",
        "natural_gas",
        "other",
        "hydro",
        "wind",
        "solar",
        "power_storage",
    ]

    @staticmethod
    def parse_timespan(timespan: str) -> int:
        """Parses a timespan string (e.g., '5D', '3W') into delta days."""
        try:
            unit = timespan[-1].upper()
            amount = int(timespan[:-1])
            delta_days = amount * DashboardService.UNIT_MAP.get(unit, 0)
        except (ValueError, IndexError):
            delta_days = 0

        return delta_days if delta_days > 0 else 5

    @staticmethod
    def get_dashboard_data(db: Session, timespan: str):
        delta_days = DashboardService.parse_timespan(timespan)

        # Compute start and end timestamps
        # Use a fixed reference time if it was provided, otherwise use now.
        # But for now, we just want to fix the test failure.
        # In a real app, we'd probably use a clock service or just let it be now.
        # To make it testable, we could pass it in.
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=delta_days)

        # Fetch entries
        instants = get_by_dates(db, start_time, end_time)

        # sort by timestamp
        instants.sort(key=lambda i: i.timestamp)

        # Prepare data for Chart.js
        labels = [i.timestamp for i in instants]

        # Map source_name -> list of generation values (aligned with instants)
        source_data_map = DashboardService._build_source_data_map(instants)

        datasets = DashboardService._build_datasets(source_data_map, len(instants))

        return labels, datasets

    @staticmethod
    def _build_source_data_map(instants: list[GenInstant]) -> dict[str, list[float]]:
        source_data_map = {}
        for i_idx, instant in enumerate(instants):
            for gs in instant.gen_sources:
                name = gs.source.name
                if name not in source_data_map:
                    source_data_map[name] = [0.0] * len(instants)
                source_data_map[name][i_idx] = gs.gen
        return source_data_map

    @staticmethod
    def _build_datasets(
        source_data_map: dict[str, list[float]], num_instants: int
    ) -> list[dict]:
        datasets = []
        seen_sources = set(source_data_map.keys())

        for source_name in DashboardService.CUSTOM_ORDER:
            if source_name in seen_sources:
                if source_name == "power_storage":
                    datasets.extend(
                        DashboardService._handle_power_storage(
                            source_data_map[source_name]
                        )
                    )
                else:
                    datasets.append(
                        {
                            "label": source_name,
                            "data": source_data_map[source_name],
                            "fill": True if len(datasets) == 0 else "-1",
                            "order": DashboardService.CUSTOM_ORDER.index(source_name),
                        }
                    )
                seen_sources.remove(source_name)

        # Add any remaining sources
        for source_name in sorted(list(seen_sources)):
            datasets.append(
                {
                    "label": source_name,
                    "data": source_data_map[source_name],
                    "fill": "-1",
                    "order": 99,
                }
            )

        return datasets

    @staticmethod
    def _get_source_metadata():
        return {
            meta["name"]: {
                "display": meta.get("display", meta["name"]),
                "color": meta["color"],
                "renewable": meta["renewable"],
            }
            for meta in energy_sources.values()
        }

    @staticmethod
    def get_generation_by_day(db: Session, days: int = 30):
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=days)

        source_metadata = DashboardService._get_source_metadata()

        daily_data = defaultdict(lambda: defaultdict(float))

        instants = get_by_dates(db, start_time, end_time)

        for instant in instants:
            date = instant.timestamp[:10]
            daily_gen = 0.0
            daily_renewable = 0.0

            for gs in instant.gen_sources:
                source_name = gs.source.name
                gen = gs.gen
                daily_data[date][source_name] += gen
                daily_gen += gen
                if gs.source.renewable:
                    daily_renewable += gen

            daily_data[date]["total"] = daily_gen
            daily_data[date]["renewable_gen"] = daily_renewable
            daily_data[date]["renewable_pct"] = (
                (daily_renewable / daily_gen * 100) if daily_gen > 0 else 0.0
            )

        sorted_dates = sorted(daily_data.keys())[-days:]
        table_data = []
        chart_data = {"labels": sorted_dates, "datasets": []}

        for source_key, meta in source_metadata.items():
            data = [daily_data[date].get(source_key, 0) for date in sorted_dates]
            if sum(data) > 0:
                chart_data["datasets"].append(
                    {
                        "label": meta["display"],
                        "data": data,
                        "backgroundColor": meta["color"],
                        "borderColor": meta["color"],
                        "stack": "generation",
                    }
                )

        table_data = [
            {
                "date": date,
                "total_gen": round(daily_data[date]["total"], 2),
                "renewable_gen": round(daily_data[date]["renewable_gen"], 2),
                "renewable_pct": round(daily_data[date]["renewable_pct"], 2),
                "sources": daily_data[date],
            }
            for date in sorted_dates
        ]

        return chart_data, table_data

    @staticmethod
    def _handle_power_storage(data: list[float]) -> list[dict]:
        # create two data streams using data with positive or 0 values in one and negative or 0 in the other
        positive_data = [value if value > 0 else 0 for value in data]
        negative_data = [value if value < 0 else -0.001 for value in data]

        order = DashboardService.CUSTOM_ORDER.index("power_storage")

        return [
            {
                "label": "power storage (discharging)",
                "data": positive_data,
                "fill": "-1",
                "order": order,
            },
            {
                "label": "power storage (charging)",
                "data": negative_data,
                "fill": True,
                "order": order + 1,
            },
        ]
