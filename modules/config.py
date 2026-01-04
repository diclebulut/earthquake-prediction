
#This dates need to be filled for any data interval 
START_MONTH = 11
START_YEAR = 2025
END_MONTH = 1
END_YEAR = 2026


TUPLE_COLUMNS_TO_UNPACK = ['average_dip', 'average_rake', 'lower_seis_depth', 'net_slip_rate', 'upper_seis_depth']
HIGH_MAG_THRESHOLD = 3.5
MAP_MODE = 'SIMPLE' #options: 'SIMPLE', 'FAULT_DETAIL', 'ALTERNATIVE'

OUTPUT_DIR = 'Outputs'
OUTPUT_FAULT_STATS_DIR = 'fault_stats'
OUTPUT_EQ_MAPS_DIR = 'eq_maps'

INPUT_DIR = 'Inputs'
INPUT_EQ_DIR = 'earthquake_data'
INPUT_FAULT_DIR = 'fault_data'
GEOJSON_OF_FAULTS_JSON = 'gem_active_faults.geojson'
