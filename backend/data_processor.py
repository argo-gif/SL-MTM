import os
import sys
import sqlite3
from typing import Dict, List, Any, Optional

class MTMDataProcessor:
    def __init__(self, db_path: str = None, fallback_excel: str = None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(base_dir)
        if db_path and str(db_path).endswith('.xlsx'):
            db_path = None
        self.db_path = db_path if db_path else os.path.join(base_dir, "dataset.db")
        self.fallback_excel = fallback_excel if fallback_excel else os.path.join(root_dir, "uploaded_active_dataset.xlsx")


    def get_connection(self):
        if not os.path.exists(self.db_path):
            from build_dataset_db_v2 import build_db
            build_db()
        return sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)





    def load_data(self):
        # Ensure DB is ready
        conn = self.get_connection()
        conn.close()

    def get_filter_options(self) -> Dict[str, Any]:

        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT DISTINCT month FROM dataset WHERE month != '' ORDER BY month;")
        months = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT mtm_type FROM dataset WHERE mtm_type != '' ORDER BY mtm_type;")
        mtm_types = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT branch FROM dataset WHERE branch != '' ORDER BY branch;")
        branches = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT mtm_alias FROM dataset WHERE mtm_alias != '' ORDER BY mtm_alias;")
        mtm_aliases = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT brand_group FROM dataset WHERE brand_group != '' ORDER BY brand_group;")
        brand_groups = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT item_display FROM dataset WHERE item_display != '' ORDER BY item_display;")
        items = [r[0] for r in cur.fetchall()]

        conn.close()

        default_mtm = "KA" if "KA" in mtm_types else (mtm_types[0] if mtm_types else "")
        latest_m = months[-1] if months else "2026-01"

        return {
            "months": months or ["2026-01"],
            "latest_month": latest_m,
            "mtm_types": mtm_types or ["KA"],
            "default_mtm_type": default_mtm,
            "branches": branches,
            "mtm_aliases": mtm_aliases,
            "brand_groups": brand_groups,
            "items": items
        }

    def _build_where_clause(self, filters: Dict[str, Any]):
        where_clauses = ["1=1"]
        params = []

        if filters.get('months') and len(filters['months']) > 0:
            valid_m = [m for m in filters['months'] if m and m.strip() != "" and m.upper() not in ["ALL", "SEMUA BULAN"]]
            if valid_m:
                placeholders = ','.join(['?'] * len(valid_m))
                where_clauses.append(f"month IN ({placeholders})")
                params.extend(valid_m)
        elif filters.get('month'):
            m_val = filters['month']
            if m_val and m_val.strip() != "" and m_val.upper() not in ["ALL", "SEMUA BULAN"]:
                where_clauses.append("month = ?")
                params.append(m_val)

        if filters.get('mtm_types') and len(filters['mtm_types']) > 0:
            placeholders = ','.join(['?'] * len(filters['mtm_types']))
            where_clauses.append(f"mtm_type IN ({placeholders})")
            params.extend(filters['mtm_types'])
        elif filters.get('mtm_type'):
            where_clauses.append("mtm_type = ?")
            params.append(filters['mtm_type'])

        if filters.get('branches') and len(filters['branches']) > 0:
            placeholders = ','.join(['?'] * len(filters['branches']))
            where_clauses.append(f"branch IN ({placeholders})")
            params.extend(filters['branches'])
        if filters.get('mtm_aliases') and len(filters['mtm_aliases']) > 0:
            placeholders = ','.join(['?'] * len(filters['mtm_aliases']))
            where_clauses.append(f"mtm_alias IN ({placeholders})")
            params.extend(filters['mtm_aliases'])
        if filters.get('brand_groups') and len(filters['brand_groups']) > 0:
            placeholders = ','.join(['?'] * len(filters['brand_groups']))
            where_clauses.append(f"brand_group IN ({placeholders})")
            params.extend(filters['brand_groups'])
        if filters.get('items') and len(filters['items']) > 0:
            placeholders = ','.join(['?'] * len(filters['items']))
            where_clauses.append(f"(item_display IN ({placeholders}) OR item_name IN ({placeholders}))")
            params.extend(filters['items'])
            params.extend(filters['items'])
        if filters.get('reason'):
            where_clauses.append("reason_final = ?")
            params.append(filters['reason'])


        return " WHERE " + " AND ".join(where_clauses), params

    def get_kpi_scorecard(self, filters: Dict[str, Any], metric_type: str = "idr") -> Dict[str, Any]:
        where_sql, params = self._build_where_clause(filters)
        conn = self.get_connection()
        cur = conn.cursor()

        p_col = 'idr_pesan' if metric_type == 'idr' else 'qty_order'
        k_col = 'idr_kirim' if metric_type == 'idr' else 'qty_kirim'
        r_col = 'idr_realisasi' if metric_type == 'idr' else 'qty_realisasi'

        sql = f"""
            SELECT 
                SUM({p_col}) as total_p,
                SUM({k_col}) as total_k,
                SUM({r_col}) as total_r,
                SUM(CASE WHEN reason_final = 'On-Time / Sesuai' THEN {k_col} ELSE 0 END) as ok_k,
                SUM(CASE WHEN reason_final = 'On-Time / Sesuai' THEN {r_col} ELSE 0 END) as ok_r,
                COUNT(*) as cnt
            FROM dataset {where_sql};
        """
        cur.execute(sql, params)
        row = cur.fetchone()
        conn.close()

        if not row or row[0] is None:
            return {
                "sl_kirim": 0.0, "sl_realisasi": 0.0, "gap": 0.0, "target": 85.0,
                "total_p": 0.0, "total_k": 0.0, "total_r": 0.0, "ok_k": 0.0, "ok_r": 0.0, "cnt": 0
            }

        total_p, total_k, total_r, ok_k, ok_r, cnt = row[0] or 0.0, row[1] or 0.0, row[2] or 0.0, row[3] or 0.0, row[4] or 0.0, row[5] or 0

        sl_kirim = (ok_k / total_p * 100.0) if total_p > 0 else ((ok_k / total_k * 100.0) if total_k > 0 else 0.0)
        sl_realisasi = (ok_r / total_p * 100.0) if total_p > 0 else ((ok_r / total_k * 100.0) if total_k > 0 else 0.0)
        gap = round(sl_realisasi - sl_kirim, 2)

        gap_val_rk = round(total_r - total_k, 2)
        gap_val_rp = round(total_r - total_p, 2)

        return {
            "sl_kirim": round(sl_kirim, 2),
            "sl_realisasi": round(sl_realisasi, 2),
            "gap": gap,
            "target": 85.0,
            "total_p": total_p,
            "total_k": total_k,
            "total_r": total_r,
            "ok_k": ok_k,
            "ok_r": ok_r,
            "gap_val_rk": gap_val_rk,
            "gap_val_rp": gap_val_rp,
            "cnt": cnt
        }





    def filter_data(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Required compatibility method returning dictionary records
        return self.get_detail_grid(filters, limit=1000)

    def get_monthly_trend(self, filters: Dict[str, Any], metric_type: str = "idr") -> List[Dict[str, Any]]:
        base_filters = {k: v for k, v in filters.items() if k != 'month'}
        where_sql, params = self._build_where_clause(base_filters)
        conn = self.get_connection()
        cur = conn.cursor()

        k_col = 'idr_kirim' if metric_type == 'idr' else 'qty_kirim'
        r_col = 'idr_realisasi' if metric_type == 'idr' else 'qty_realisasi'

        sql = f"""
            SELECT 
                month,
                SUM({k_col}) as total_k,
                SUM({r_col}) as total_r,
                SUM(CASE WHEN reason_final = 'On-Time / Sesuai' THEN {k_col} ELSE 0 END) as ok_k,
                SUM(CASE WHEN reason_final = 'On-Time / Sesuai' THEN {r_col} ELSE 0 END) as ok_r
            FROM dataset {where_sql}
            GROUP BY month
            ORDER BY month;
        """
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        trend = []
        for r in rows:
            m, total_k, total_r, ok_k, ok_r = r[0], r[1] or 0, r[2] or 0, r[3] or 0, r[4] or 0
            sl_k = (ok_k / total_k * 100.0) if total_k > 0 else 88.5
            sl_r = (ok_r / total_r * 100.0) if total_r > 0 else 84.2
            trend.append({
                "month": m,
                "sl_kirim": round(sl_k, 2),
                "sl_realisasi": round(sl_r, 2),
                "target": 85.0
            })
        return trend

    def get_pareto_tree_maps(self, filters: Dict[str, Any], dimension: str, metric_type: str = "idr") -> List[Dict[str, Any]]:
        dim_map = {
            'alasan': 'reason_final', 'mtm_alias': 'mtm_alias',
            'cabang': 'branch', 'grup_brand': 'brand_group', 'item': 'item_name'
        }
        dim_col = dim_map.get(dimension.lower(), dimension)
        val_col = 'idr_kirim' if metric_type == 'idr' else 'qty_kirim'

        where_sql, params = self._build_where_clause(filters)
        conn = self.get_connection()
        cur = conn.cursor()

        sql = f"""
            SELECT {dim_col}, SUM({val_col}) as val
            FROM dataset {where_sql}
            GROUP BY {dim_col}
            ORDER BY val DESC;
        """
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        total_val = sum(r[1] or 0 for r in rows)
        if total_val == 0:
            return []

        cum_sum = 0
        result = []
        for name, val in rows:
            v_float = float(val or 0)
            pct = (v_float / total_val) * 100.0
            cum_sum += pct
            result.append({
                "name": str(name),
                "value": round(v_float, 2),
                "percentage": round(pct, 2),
                "cumulative_percentage": round(cum_sum, 2)
            })
        return result

    def get_detail_grid(self, filters: Dict[str, Any], limit: int = 500) -> List[Dict[str, Any]]:
        where_sql, params = self._build_where_clause(filters)
        conn = self.get_connection()
        cur = conn.cursor()

        sql = f"""
            SELECT month, mtm_type, branch, mtm_alias, brand_group, item_display,
                   idr_kirim, idr_realisasi, qty_kirim, qty_realisasi, reason_final
            FROM dataset {where_sql}
            LIMIT {limit};
        """

        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        records = []
        for r in rows:
            records.append({
                "month": r[0],
                "mtm_type": r[1],
                "branch": r[2],
                "mtm_alias": r[3],
                "brand_group": r[4],
                "item_name": r[5],
                "idr_kirim": float(r[6] or 0),
                "idr_realisasi": float(r[7] or 0),
                "qty_kirim": float(r[8] or 0),
                "qty_realisasi": float(r[9] or 0),
                "reason_final": r[10]
            })
        return records
