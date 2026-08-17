import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data_processor import MTMDataProcessor

def run_test():
    print("Initializing MTMDataProcessor with SQLite Database...")
    processor = MTMDataProcessor("backend/dataset.db")
    processor.load_data()
    
    print("\n--- Testing Filter Options on Full Dataset ---")
    options = processor.get_filter_options()
    print("Available Months:", options["months"])
    print("Latest Month:", options["latest_month"])
    print("Available MTM Types:", options["mtm_types"])
    print("Default MTM Type:", options["default_mtm_type"])
    print("Total Unique Branches:", len(options["branches"]))
    print("Total Unique MTM Aliases:", len(options["mtm_aliases"]))
    print("Total Unique Brand Groups:", len(options["brand_groups"]))
    print("Total Unique Items:", len(options["items"]))
    
    print("\n--- Testing Filtered KPI Scorecard ---")
    filters = {
        "month": options["latest_month"],
        "mtm_type": options["default_mtm_type"]
    }
    
    scorecard_idr = processor.get_kpi_scorecard(filters, metric_type="idr")
    scorecard_qty = processor.get_kpi_scorecard(filters, metric_type="qty")
    print("KPI Scorecard (IDR):", scorecard_idr)
    print("KPI Scorecard (QTY):", scorecard_qty)
    
    print("\n--- Testing Pareto Tree Maps (Alasan) ---")
    pareto_alasan = processor.get_pareto_tree_maps(filters, dimension="alasan", metric_type="idr")
    print(f"Pareto Alasan Count: {len(pareto_alasan)}")
    if pareto_alasan:
        print("Top 3 Alasan:", pareto_alasan[:3])
        
    print("\n--- Testing Pareto Tree Maps (Cabang) ---")
    pareto_cabang = processor.get_pareto_tree_maps(filters, dimension="cabang", metric_type="idr")
    print(f"Pareto Cabang Count: {len(pareto_cabang)}")
    if pareto_cabang:
        print("Top 3 Cabang:", pareto_cabang[:3])

    print("\n--- Data Processor Unit Test PASSED! ---")

if __name__ == "__main__":
    run_test()
