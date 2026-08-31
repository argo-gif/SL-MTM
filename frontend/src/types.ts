export interface User {
  username: string;
  role: 'admin' | 'user';
  can_upload: boolean;
  token?: string;
}

export interface KPIScorecard {
  sl_kirim: number;
  sl_realisasi: number;
  gap: number;
  target: number;
}

export interface MonthlyTrendItem {
  month: string;
  sl_kirim: number;
  sl_realisasi: number;
  target: number;
}

export interface ParetoItem {
  name: string;
  value: number;
  percentage: number;
  cumulative_percentage: number;
}

export interface FilterOptions {
  months: string[];
  latest_month: string;
  mtm_types: string[];
  default_mtm_type: string;
  branches: string[];
  mtm_aliases: string[];
  brand_groups: string[];
  items: string[];
}

export interface ActiveFilters {
  months?: string[];
  month: string;
  mtm_types?: string[];
  mtm_type: string;
  branches: string[];
  mtm_aliases: string[];
  brand_groups: string[];
  items: string[];
  reason?: string;
  metric_type: 'idr' | 'qty';
  sl_type?: 'sl_kirim' | 'sl_realisasi' | string;
}

export interface GridRecord {
  month: string;
  mtm_type: string;
  branch: string;
  mtm_alias: string;
  brand_group: string;
  item_name: string;
  idr_kirim: number;
  idr_realisasi: number;
  qty_kirim: number;
  qty_realisasi: number;
  reason_final: string;
}
