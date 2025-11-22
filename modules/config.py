
#This dates need to be filled for any data interval 
START_MONTH = 9
START_YEAR = 2025
END_MONTH = 11
END_YEAR = 2025

DATE_INTERVAL = 'LAST_2_DAYS' #options: 'LAST_2_DAYS', 'FULL_DATASET'
GEOJSON_OF_FAULTS_PATH = 'faults/gem_active_faults.geojson'

TUPLE_COLUMNS_TO_UNPACK = ['average_dip', 'average_rake', 'lower_seis_depth', 'net_slip_rate', 'upper_seis_depth']
HIGH_MAG_THRESHOLD = 3.5
MAP_MODE = 'SIMPLE' #options: 'SIMPLE', 'FAULT_DETAIL', 'ALTERNATIVE'
