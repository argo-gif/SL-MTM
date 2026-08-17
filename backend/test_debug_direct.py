import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data_processor import MTMDataProcessor

try:
    print("Testing MTMDataProcessor.get_filter_options()...")
    p = MTMDataProcessor()
    opts = p.get_filter_options()
    print("SUCCESS! Filter options retrieved:")
    print("  Months:", opts["months"])
    print("  Latest Month:", opts["latest_month"])
    print("  MTM Types:", opts["mtm_types"])
    print("  Branches:", len(opts["branches"]))
except Exception:
    traceback.print_exc()
