#!/usr/bin/env python3
"""Independent numerical feasibility recomputation for the 2021 C case.

This module deliberately does not call the optimizer.  It reconstructs balances from
the emitted sparse order/transport records so an optimizer status cannot substitute
for a business-feasibility check.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

CONSUMPTION = {"A": 0.60, "B": 0.66, "C": 0.72}
PURCHASE_PRICE = {"A": 1.20, "B": 1.10, "C": 1.00}


def _finite_nonnegative(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) >= 0.0
    )


def verify_plan(
    plan: dict[str, Any],
    *,
    supplier_types: dict[str, str],
    delivery_ratios: dict[str, float],
    carrier_loss_rates: dict[str, float],
    weekly_demand_product_m3: float | None,
    carrier_capacity_m3: float,
) -> dict[str, Any]:
    """Recompute all balances from sparse records using an independent data path."""

    violations: list[str] = []
    order_by_supplier: dict[str, float] = defaultdict(float)
    shipped_by_supplier: dict[str, float] = defaultdict(float)
    shipped_by_carrier: dict[str, float] = defaultdict(float)
    carrier_set_by_supplier: dict[str, set[str]] = defaultdict(set)
    effective_received = 0.0
    purchase_cost = 0.0
    raw_received = 0.0
    capacity_tolerance = 1e-6 * max(1.0, carrier_capacity_m3)
    demand_tolerance = (
        0.0 if weekly_demand_product_m3 is None else 1e-6 * max(1.0, weekly_demand_product_m3)
    )

    orders = plan.get("orders", [])
    transport = plan.get("transport", [])
    if not isinstance(orders, list) or not isinstance(transport, list):
        return {"feasible": False, "violations": ["RECORD_COLLECTION_INVALID"]}

    for record in orders:
        if not isinstance(record, dict) or set(record) != {"supplier_id", "volume_m3"}:
            violations.append("ORDER_RECORD_INVALID")
            continue
        supplier = record.get("supplier_id")
        volume = record.get("volume_m3")
        if supplier not in supplier_types or not _finite_nonnegative(volume):
            violations.append("ORDER_VALUE_INVALID")
            continue
        order_by_supplier[str(supplier)] += float(volume)
        purchase_cost += float(volume) * PURCHASE_PRICE[supplier_types[str(supplier)]]

    for record in transport:
        if not isinstance(record, dict) or set(record) != {
            "carrier_id",
            "supplier_id",
            "volume_m3",
        }:
            violations.append("TRANSPORT_RECORD_INVALID")
            continue
        supplier = record.get("supplier_id")
        carrier = record.get("carrier_id")
        volume = record.get("volume_m3")
        if (
            supplier not in supplier_types
            or carrier not in carrier_loss_rates
            or not _finite_nonnegative(volume)
        ):
            violations.append("TRANSPORT_VALUE_INVALID")
            continue
        supplier = str(supplier)
        carrier = str(carrier)
        volume = float(volume)
        shipped_by_supplier[supplier] += volume
        shipped_by_carrier[carrier] += volume
        if volume > 1e-7:
            carrier_set_by_supplier[supplier].add(carrier)
        received = volume * (1.0 - float(carrier_loss_rates[carrier]))
        raw_received += received
        effective_received += received / CONSUMPTION[supplier_types[supplier]]

    for supplier, order_volume in order_by_supplier.items():
        expected_shipment = order_volume * float(delivery_ratios[supplier])
        observed_shipment = shipped_by_supplier.get(supplier, 0.0)
        tolerance = 1e-5 * max(1.0, expected_shipment)
        if abs(expected_shipment - observed_shipment) > tolerance:
            violations.append(f"SUPPLIER_BALANCE:{supplier}")
    unexpected = set(shipped_by_supplier) - set(order_by_supplier)
    if unexpected:
        violations.append("SHIPMENT_WITHOUT_ORDER")
    for carrier, volume in shipped_by_carrier.items():
        if volume > carrier_capacity_m3 + capacity_tolerance:
            violations.append(f"CARRIER_CAPACITY:{carrier}")

    inventory_trace: list[float] = []
    minimum_inventory = None
    if weekly_demand_product_m3 is not None:
        initial_inventory = 2.0 * weekly_demand_product_m3
        inventory = initial_inventory
        for _ in range(24):
            inventory += effective_received - weekly_demand_product_m3
            inventory_trace.append(inventory)
        minimum_inventory = min(inventory_trace)
        if effective_received + demand_tolerance < weekly_demand_product_m3:
            violations.append("WEEKLY_PRODUCTION_REQUIREMENT")
        if minimum_inventory + 24.0 * demand_tolerance < 2.0 * weekly_demand_product_m3:
            violations.append("TWO_WEEK_INVENTORY_FLOOR")

    split_supplier_count = sum(len(carriers) > 1 for carriers in carrier_set_by_supplier.values())
    return {
        "feasible": not violations,
        "violations": sorted(set(violations)),
        "weekly_effective_received_product_m3": round(effective_received, 6),
        "weekly_raw_received_m3": round(raw_received, 6),
        "weekly_normalized_purchase_cost": round(purchase_cost, 6),
        "maximum_carrier_load_m3": round(max(shipped_by_carrier.values(), default=0.0), 6),
        "minimum_inventory_product_m3": (
            None if minimum_inventory is None else round(minimum_inventory, 6)
        ),
        "selected_supplier_count": len([v for v in order_by_supplier.values() if v > 1e-7]),
        "split_supplier_count": split_supplier_count,
        "numerical_tolerance_m3": round(max(capacity_tolerance, demand_tolerance), 9),
    }
