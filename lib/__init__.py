# Use absolute imports for standalone package
try:
    from drug_database import load_drug_data
    from dst_calc import *
    from supp_calc import *
except ImportError:
    # Fallback for when used as part of a larger package
    from .drug_database import load_drug_data
    from .dst_calc import *
    from .supp_calc import *



