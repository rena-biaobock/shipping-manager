from datetime import datetime, timedelta

EXCEL_EPOCH = datetime(1899, 12, 30)


def excel_serial_to_dt(serial: float) -> datetime:
    return EXCEL_EPOCH + timedelta(days=serial)
