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

    def get_filter_options(self, active_filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        conn = self.get_connection()
        cur = conn.cursor()

        # Always fetch months sorted DESCENDING (latest month first!)
        cur.execute("SELECT DISTINCT month FROM dataset WHERE month != '' ORDER BY month DESC;")
        months = [r[0] for r in cur.fetchall()]

        active_filters = active_filters or {}

        def get_distinct_options(target_field: str):
            # Omit current target_field from sub_filters so user can see available options in target_field
            sub_filters = {}
            for k, v in active_filters.items():
                if k in ['month', 'months', 'mtm_type', 'mtm_types', 'branch', 'branches', 'mtm_alias', 'mtm_aliases', 'brand_group', 'brand_groups', 'item', 'items']:
                    if k not in [target_field, f"{target_field}s", f"{target_field}_group", f"{target_field}_groups"]:
                        sub_filters[k] = v

            where_sql, params = self._build_where_clause(sub_filters)
            db_col = 'reason_final' if target_field == 'reason' else ('item_display' if target_field == 'item' else target_field)
            query = f"SELECT DISTINCT {db_col} FROM dataset {where_sql} AND {db_col} != '' ORDER BY {db_col};"
            cur.execute(query, params)
            return [r[0] for r in cur.fetchall()]

        mtm_types = get_distinct_options('mtm_type')
        branches = get_distinct_options('branch')
        mtm_aliases = get_distinct_options('mtm_alias')
        brand_groups = get_distinct_options('brand_group')
        items = get_distinct_options('item')
        raw_reasons = get_distinct_options('reason')
        problem_reasons = [r for r in raw_reasons if r and r != 'On-Time / Sesuai' and r != 'Fulfill']
        reasons = ['Fulfill'] + problem_reasons

        conn.close()

        default_mtm = "KA" if "KA" in mtm_types else (mtm_types[0] if mtm_types else "")
        latest_m = months[0] if months else "2026-08"

        import datetime
        db_file = self.db_path if os.path.exists(self.db_path) else self.fallback_excel
        last_update_str = "-"
        if os.path.exists(db_file):
            mtime = os.path.getmtime(db_file)
            last_update_str = datetime.datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")

        return {
            "months": months or ["2026-08"],
            "latest_month": latest_m,
            "last_update": last_update_str,
            "mtm_types": mtm_types or ["KA"],
            "default_mtm_type": default_mtm,
            "branches": branches,
            "mtm_aliases": mtm_aliases,
            "brand_groups": brand_groups,
            "items": items,
            "reasons": reasons
        }

    def _build_where_clause(self, filters: Dict[str, Any]):
        where_clauses = ["1=1"]
        params = []

        def clean_vals(arr):
            if not arr: return []
            if isinstance(arr, str): arr = [arr]
            return [
                v for v in arr 
                if v and str(v).strip() != "" and str(v).upper() not in ["ALL", "SEMUA BULAN", "SEMUA JENIS MTM", "SEMUA CABANG", "SEMUA ALIAS", "SEMUA GRUP BRAND", "SEMUA PRODUK / ITEM", "SEMUA ALASAN", "SEMUA"]
            ]

        def normalize_month(v):
            v_str = str(v).strip().upper()
            if not v_str or v_str in ["ALL", "SEMUA BULAN", "SEMUA"]:
                return None
            if len(v_str) == 7 and v_str[4] == '-' and v_str[:4].isdigit() and v_str[5:].isdigit():
                return v_str
            month_name_map = {
                'JAN': '01', 'JANUARI': '01',
                'FEB': '02', 'PEB': '02', 'PEBRUARI': '02', 'FEBRUARI': '02',
                'MAR': '03', 'MARET': '03',
                'APR': '04', 'APRIL': '04',
                'MEI': '05', 'MAY': '05',
                'JUN': '06', 'JUNI': '06',
                'JUL': '07', 'JULI': '07',
                'AGU': '08', 'AUG': '08', 'AGUSTUS': '08',
                'SEP': '09', 'SEPTEMBER': '09',
                'OKT': '10', 'OCT': '10', 'OKTOBER': '10',
                'NOV': '11', 'NOVEMBER': '11',
                'DES': '12', 'DEC': '12', 'DESEMBER': '12'
            }
            for sep in ['-', ' ', '/']:
                if sep in v_str:
                    parts = v_str.split(sep)
                    if len(parts) == 2:
                        p1, p2 = parts[0].strip(), parts[1].strip()
                        if p1 in month_name_map and p2.isdigit() and len(p2) == 4:
                            return f"{p2}-{month_name_map[p1]}"
                        if p2 in month_name_map and p1.isdigit() and len(p1) == 4:
                            return f"{p1}-{month_name_map[p2]}"
            return v_str

        raw_m = clean_vals(filters.get('months')) or clean_vals(filters.get('month'))
        valid_m = []
        for m in raw_m:
            nm = normalize_month(m)
            if nm and nm not in valid_m:
                valid_m.append(nm)

        if valid_m:
            placeholders = ','.join(['?'] * len(valid_m))
            where_clauses.append(f"month IN ({placeholders})")
            params.extend(valid_m)

        valid_t = clean_vals(filters.get('mtm_types')) or clean_vals(filters.get('mtm_type'))
        if valid_t:
            placeholders = ','.join(['?'] * len(valid_t))
            where_clauses.append(f"mtm_type IN ({placeholders})")
            params.extend(valid_t)

        valid_b = clean_vals(filters.get('branches')) or clean_vals(filters.get('branch'))
        if valid_b:
            placeholders = ','.join(['?'] * len(valid_b))
            where_clauses.append(f"branch IN ({placeholders})")
            params.extend(valid_b)

        valid_a = clean_vals(filters.get('mtm_aliases')) or clean_vals(filters.get('mtm_alias'))
        if valid_a:
            placeholders = ','.join(['?'] * len(valid_a))
            where_clauses.append(f"mtm_alias IN ({placeholders})")
            params.extend(valid_a)

        valid_bg = clean_vals(filters.get('brand_groups')) or clean_vals(filters.get('brand_group'))
        if valid_bg:
            placeholders = ','.join(['?'] * len(valid_bg))
            where_clauses.append(f"brand_group IN ({placeholders})")
            params.extend(valid_bg)

        valid_i = clean_vals(filters.get('items')) or clean_vals(filters.get('item'))
        if valid_i:
            displays = []
            codes = []
            names = []
            for v in valid_i:
                v_str = str(v).strip()
                displays.append(v_str)
                if ' - ' in v_str:
                    parts = v_str.split(' - ', 1)
                    codes.append(parts[0].strip())
                    names.append(parts[1].strip())
                else:
                    codes.append(v_str)
                    names.append(v_str)

            p_disp = ','.join(['?'] * len(displays))
            p_code = ','.join(['?'] * len(codes))
            p_name = ','.join(['?'] * len(names))

            where_clauses.append(f"(item_display IN ({p_disp}) OR product_code IN ({p_code}) OR item_name IN ({p_name}))")
            params.extend(displays)
            params.extend(codes)
            params.extend(names)

        valid_r = clean_vals(filters.get('reasons')) or clean_vals(filters.get('reason'))
        if valid_r:
            has_fulfill = any(r in ['Fulfill', 'FULFILL', 'On-Time / Sesuai', 'ON-TIME / SESUAI'] for r in valid_r)
            non_fulfill = [r for r in valid_r if r not in ['Fulfill', 'FULFILL', 'On-Time / Sesuai', 'ON-TIME / SESUAI']]
            
            conds = []
            if non_fulfill:
                placeholders = ','.join(['?'] * len(non_fulfill))
                conds.append(f"reason_final IN ({placeholders})")
                params.extend(non_fulfill)
            if has_fulfill:
                conds.append("reason_final = 'On-Time / Sesuai'")
            
            if conds:
                where_clauses.append("(" + " OR ".join(conds) + ")")

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
        # Extract max month filter if specified
        max_month = None
        if filters.get('months'):
            valid_m = [m for m in filters['months'] if m and m != 'Semua Bulan']
            if valid_m:
                max_month = max(valid_m)
        elif filters.get('month') and filters['month'] != 'Semua Bulan':
            max_month = filters['month']

        base_filters = {k: v for k, v in filters.items() if k not in ['month', 'months']}
        where_sql, params = self._build_where_clause(base_filters)

        if max_month:
            where_sql += " AND month <= ?" if "WHERE" in where_sql else " WHERE month <= ?"
            params.append(max_month)

        conn = self.get_connection()
        cur = conn.cursor()

        p_col = 'idr_pesan' if metric_type == 'idr' else 'qty_order'
        k_col = 'idr_kirim' if metric_type == 'idr' else 'qty_kirim'
        r_col = 'idr_realisasi' if metric_type == 'idr' else 'qty_realisasi'

        sql = f"""
            SELECT 
                month,
                SUM({p_col}) as total_p,
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
            m = r[0]
            total_p = r[1] or 0.0
            total_k = r[2] or 0.0
            total_r = r[3] or 0.0
            ok_k = r[4] or 0.0
            ok_r = r[5] or 0.0

            sl_k = (ok_k / total_p * 100.0) if total_p > 0 else ((ok_k / total_k * 100.0) if total_k > 0 else 0.0)
            sl_r = (ok_r / total_p * 100.0) if total_p > 0 else ((ok_r / total_k * 100.0) if total_k > 0 else 0.0)
            gap = round(sl_r - sl_k, 2)

            trend.append({
                "month": m,
                "total_p": total_p,
                "total_k": total_k,
                "total_r": total_r,
                "ok_k": ok_k,
                "ok_r": ok_r,
                "sl_kirim": round(sl_k, 2),
                "sl_realisasi": round(sl_r, 2),
                "gap": gap,
                "target": 85.0
            })
        return trend


    def get_pareto_tree_maps(self, filters: Dict[str, Any], dimension: str, metric_type: str = "idr", unfulfill_only: bool = True) -> List[Dict[str, Any]]:
        dim_map = {
            'alasan': 'reason_final', 'mtm_alias': 'mtm_alias',
            'cabang': 'branch', 'grup_brand': 'brand_group', 'item': 'item_name'
        }
        dim_col = dim_map.get(dimension.lower(), dimension)

        metric_type = filters.get('metric_type', metric_type)
        is_unfulfill = unfulfill_only if 'unfulfill_only' in filters is False else filters.get('unfulfill_only', unfulfill_only)

        if is_unfulfill:
            val_col = "(CASE WHEN (idr_pesan - idr_kirim) > 0 THEN (idr_pesan - idr_kirim) ELSE idr_pesan END)" if metric_type == 'idr' else "(CASE WHEN (qty_order - qty_kirim) > 0 THEN (qty_order - qty_kirim) ELSE qty_order END)"
        else:
            val_col = 'idr_kirim' if metric_type == 'idr' else 'qty_kirim'

        where_sql, params = self._build_where_clause(filters)

        if is_unfulfill:
            where_sql += " AND reason_final != 'On-Time / Sesuai'" if "WHERE" in where_sql else " WHERE reason_final != 'On-Time / Sesuai'"

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



    def get_detail_grid(self, filters: Dict[str, Any], dimension: str = "alasan", metric_type: str = "idr", limit: int = 500) -> List[Dict[str, Any]]:
        dim_map = {
            'alasan': 'reason_final', 'mtm_alias': 'mtm_alias',
            'cabang': 'branch', 'grup_brand': 'brand_group', 'item': 'item_name'
        }
        dim_col = dim_map.get(dimension.lower(), 'reason_final')

        p_col = 'idr_pesan' if metric_type == 'idr' else 'qty_order'
        k_col = 'idr_kirim' if metric_type == 'idr' else 'qty_kirim'
        r_col = 'idr_realisasi' if metric_type == 'idr' else 'qty_realisasi'

        where_sql, params = self._build_where_clause(filters)

        # If dimension is 'alasan', filter out 'On-Time / Sesuai' so reason table focuses on problem causes
        if dimension.lower() == 'alasan':
            where_sql += " AND reason_final != 'On-Time / Sesuai'" if "WHERE" in where_sql else " WHERE reason_final != 'On-Time / Sesuai'"

        conn = self.get_connection()
        cur = conn.cursor()

        sql = f"""
            SELECT 
                {dim_col} as name,
                COUNT(*) as total_trx,
                SUM({p_col}) as total_p,
                SUM({k_col}) as total_k,
                SUM({r_col}) as total_r,
                SUM(CASE WHEN reason_final != 'On-Time / Sesuai' THEN (CASE WHEN ({p_col} - {k_col}) > 0 THEN ({p_col} - {k_col}) ELSE {p_col} END) ELSE 0 END) as gap_unfulfill
            FROM dataset {where_sql}
            GROUP BY {dim_col}
            ORDER BY gap_unfulfill DESC
            LIMIT {limit};
        """


        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        total_gap_all = sum(float(r[5] or 0) for r in rows)
        cum_pct = 0.0

        records = []
        for r in rows:
            name = str(r[0] or 'Lainnya')
            total_trx = int(r[1] or 0)
            total_p = float(r[2] or 0)
            total_k = float(r[3] or 0)
            total_r = float(r[4] or 0)
            gap_unfulfill = float(r[5] or 0)

            sl_k = (total_k / total_p * 100.0) if total_p > 0 else 0.0
            sl_r = (total_r / total_p * 100.0) if total_p > 0 else 0.0

            pct = (gap_unfulfill / total_gap_all * 100.0) if total_gap_all > 0 else 0.0
            cum_pct += pct

            records.append({
                "dimension": dimension,
                "name": name,
                "total_trx": total_trx,
                "total_pesan": round(total_p, 2),
                "total_kirim": round(total_k, 2),
                "total_realisasi": round(total_r, 2),
                "gap_unfulfill": round(gap_unfulfill, 2),
                "sl_kirim": round(sl_k, 2),
                "sl_realisasi": round(sl_r, 2),
                "percentage": round(pct, 2),
                "cumulative_percentage": round(cum_pct, 2),
                "is_vital": cum_pct <= 80.0 or (len(records) == 0)
            })


        return records

