#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一策略标的池落库工具

功能:
- 将各策略筛选结果落存到 `strategy_candidates` 表
- 使用 (dt, strategy_type, code) 作为幂等键进行 UPSERT

使用:
from src.integration.strategy_persistence import save_strategy_candidates
"""

from __future__ import annotations

import json
from datetime import date
from typing import Dict, Any, List, Tuple

from sqlalchemy import create_engine, text

from config.settings import DATABASE_CONFIG


def _create_engine():
    """Create SQLAlchemy engine from global DATABASE_CONFIG."""
    connection_string = (
        f"mysql+pymysql://{DATABASE_CONFIG['username']}:{DATABASE_CONFIG['password']}"
        f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}"
        f"/{DATABASE_CONFIG['database']}?charset={DATABASE_CONFIG['charset']}"
    )
    engine = create_engine(
        connection_string,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        connect_args={
            "connect_timeout": 30,
            "read_timeout": 120,
            "write_timeout": 120,
            "charset": "utf8mb4",
        },
    )
    return engine


def _build_rows(
    dt: date,
    strategy_type: str,
    results: Dict[str, Dict[str, Any]],
    stock_info: Dict[str, Dict[str, Any]] | None,
    data_frequency: str,
    data_window_days: int | None,
) -> List[Dict[str, Any]]:
    """Convert strategy result dict to list of DB row dicts with ranks.

    results: { code: { 'volatility': float, 'sharpe': float, 'name': str, 'market_cap_category': str,
                        'market_value': float, 'data': DataFrame, 't2_entry_info': Optional[dict] } }
    stock_info: { code: { 'ipo_date': str, ... } }
    """
    # 排名：按夏普降序，其次按波动率降序
    sorted_items: List[Tuple[str, Dict[str, Any]]] = sorted(
        results.items(),
        key=lambda kv: (kv[1].get("sharpe", 0.0), kv[1].get("volatility", 0.0)),
        reverse=True,
    )

    rows: List[Dict[str, Any]] = []
    for rank, (code, info) in enumerate(sorted_items, start=1):
        base_info = stock_info.get(code, {}) if stock_info else {}
        t2 = info.get("t2_entry_info") or {}

        row = {
            "dt": dt.isoformat(),
            "strategy_type": strategy_type,
            "code": code,
            "name": info.get("name", code),
            "market_cap_category": info.get("market_cap_category"),
            "market_value_bil": info.get("market_value"),
            "ipo_date": base_info.get("ipo_date"),
            "volatility_annualized": float(info.get("volatility", 0.0) or 0.0),
            "sharpe_ratio": float(info.get("sharpe", 0.0) or 0.0),
            "rank_in_dt": rank,
            "score": None,
            "t2_date": str(t2.get("t2_date")) if t2.get("t2_date") is not None else None,
            "entry_date": str(t2.get("entry_date")) if t2.get("entry_date") is not None else None,
            "entry_price": float(t2.get("entry_price")) if t2.get("entry_price") is not None else None,
            "data_frequency": data_frequency,
            "data_window_days": data_window_days,
            "extras": json.dumps(
                {
                    "t1_date": str(t2.get("t1_date")) if t2.get("t1_date") is not None else None,
                    "t1_price": t2.get("t1_price"),
                    "t2_price": t2.get("t2_price"),
                    "wait_periods": t2.get("wait_periods"),
                }
            ),
        }
        rows.append(row)
    return rows


def save_strategy_candidates(
    dt: date,
    strategy_type: str,
    results: Dict[str, Dict[str, Any]],
    stock_info: Dict[str, Dict[str, Any]] | None = None,
    data_frequency: str = "weekly",
    data_window_days: int | None = None,
) -> int:
    """Persist candidates to DB with idempotent upsert.

    Returns number of rows written.
    """
    if not results:
        return 0

    engine = _create_engine()
    rows = _build_rows(dt, strategy_type, results, stock_info, data_frequency, data_window_days)

    sql = text(
        """
        INSERT INTO strategy_candidates (
            dt, strategy_type, code, name, market_cap_category, market_value_bil, ipo_date,
            volatility_annualized, sharpe_ratio, rank_in_dt, score,
            t2_date, entry_date, entry_price, data_frequency, data_window_days, extras
        ) VALUES (
            :dt, :strategy_type, :code, :name, :market_cap_category, :market_value_bil, :ipo_date,
            :volatility_annualized, :sharpe_ratio, :rank_in_dt, :score,
            :t2_date, :entry_date, :entry_price, :data_frequency, :data_window_days, :extras
        )
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            market_cap_category = VALUES(market_cap_category),
            market_value_bil = VALUES(market_value_bil),
            ipo_date = VALUES(ipo_date),
            volatility_annualized = VALUES(volatility_annualized),
            sharpe_ratio = VALUES(sharpe_ratio),
            rank_in_dt = VALUES(rank_in_dt),
            score = VALUES(score),
            t2_date = VALUES(t2_date),
            entry_date = VALUES(entry_date),
            entry_price = VALUES(entry_price),
            data_frequency = VALUES(data_frequency),
            data_window_days = VALUES(data_window_days),
            extras = VALUES(extras)
        """
    )

    affected = 0
    with engine.begin() as conn:
        conn.execute(sql, rows)
        affected = len(rows)

    try:
        engine.dispose()
    except Exception:
        pass
    return affected


def save_pivot_points(
    dt: date,
    code: str,
    data_frequency: str,
    pivot_result: Dict[str, Any],
    data_index: List[Any],
    prices_high: List[float] | None,
    prices_low: List[float] | None,
    is_filtered: bool = True,
) -> int:
    """Persist pivot points (highs and lows) to pivot_points table using upsert.

    pivot_result keys expected: filtered_pivot_highs, filtered_pivot_lows, pivot_meta
    data_index: pandas.DatetimeIndex or list of dates aligned to data used by analyzer
    prices_high/low: arrays to fetch exact price at pivot
    """
    if not pivot_result:
        return 0

    highs = pivot_result.get('filtered_pivot_highs', []) if is_filtered else pivot_result.get('raw_pivot_highs', [])
    lows = pivot_result.get('filtered_pivot_lows', []) if is_filtered else pivot_result.get('raw_pivot_lows', [])
    meta = (pivot_result.get('pivot_meta') or {})
    meta_high = meta.get('pivot_meta_highs', {}) if isinstance(meta, dict) else {}
    meta_low = meta.get('pivot_meta_lows', {}) if isinstance(meta, dict) else {}

    def row_from_idx(idx: int, is_high_flag: int) -> Dict[str, Any]:
        trade_dt = str(data_index[idx]) if idx < len(data_index) else None
        if trade_dt and ' ' in trade_dt:
            trade_dt = trade_dt.split(' ')[0]
        price_val = None
        if is_high_flag == 1 and prices_high is not None and idx < len(prices_high):
            try:
                price_val = float(prices_high[idx])
            except Exception:
                price_val = None
        if is_high_flag == 0 and prices_low is not None and idx < len(prices_low):
            try:
                price_val = float(prices_low[idx])
            except Exception:
                price_val = None
        m = meta_high.get(idx, {}) if is_high_flag == 1 else meta_low.get(idx, {})
        return {
            'dt': dt.isoformat(),
            'code': code,
            'data_frequency': data_frequency,
            'is_filtered': 1 if is_filtered else 0,
            'is_high': is_high_flag,
            'trade_date': trade_dt,
            'bar_index': int(idx),
            'price': price_val,
            'prominence': float(m.get('prominence')) if m.get('prominence') is not None else None,
            'confirm_strength': float(m.get('confirm_move')) if m.get('confirm_move') is not None else None,
            'z_score': float(m.get('z_left')) if m.get('z_left') is not None else None,
            'atr_pct': float(m.get('atr_pct')) if m.get('atr_pct') is not None else None,
            'extras': json.dumps(m) if isinstance(m, dict) and m else None,
        }

    rows: List[Dict[str, Any]] = []
    for idx in highs or []:
        if isinstance(idx, (int,)) and 0 <= idx < len(data_index):
            rows.append(row_from_idx(idx, 1))
    for idx in lows or []:
        if isinstance(idx, (int,)) and 0 <= idx < len(data_index):
            rows.append(row_from_idx(idx, 0))

    if not rows:
        return 0

    engine = _create_engine()
    sql = text(
        """
        INSERT INTO pivot_points (
            dt, code, data_frequency, is_filtered, is_high, trade_date,
            bar_index, price, prominence, confirm_strength, z_score, atr_pct, extras
        ) VALUES (
            :dt, :code, :data_frequency, :is_filtered, :is_high, :trade_date,
            :bar_index, :price, :prominence, :confirm_strength, :z_score, :atr_pct, :extras
        )
        ON DUPLICATE KEY UPDATE
            bar_index = VALUES(bar_index),
            price = VALUES(price),
            prominence = VALUES(prominence),
            confirm_strength = VALUES(confirm_strength),
            z_score = VALUES(z_score),
            atr_pct = VALUES(atr_pct),
            extras = VALUES(extras)
        """
    )

    with engine.begin() as conn:
        conn.execute(sql, rows)

    try:
        engine.dispose()
    except Exception:
        pass
    return len(rows)



