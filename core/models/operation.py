from dataclasses import dataclass


@dataclass
class Operation:
    operation_id: str  # e.g. "AX5T1S-112"
    code_trailer: str  # e.g. "TA487PZ"
    code_container: str  # e.g. "BSE1212"
    cod_prov: str  # e.g. "TO"
    cod_comune: str  # e.g. "A388"
    destination_port: str  # e.g. "A01"
    gps_position: tuple[float, float]  # e.g. (38.12312, 38.12312)
    documents: None  # optional, not needed

    # e.g. "2025-06-03T13:22:31"
    start_date: str
    # e.g. "2025-06-03T13:22:31"
    operation_date: str
    # e.g. "2025-06-03T15:35:12", start_date + operation_total_time
    estimated_arrival_time: str
    # e.g. 31 (fixed HH)
    operation_total_time: int
