def convert_to_datetime(timestamp_string):
    """
    Convert string to datetime in the extracted DataFrame.
    Handles multiple possible formats.
    :param timestamp_string: timestamp string
    :return: datetime or None
    """
    from datetime import datetime

    if not timestamp_string:
        return None
    timestamp_string = timestamp_string.upper()
    if timestamp_string[-1] != "Z":
        timestamp_string += "Z"

    potential_formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%MZ",
        "%Y-%m-%dT%HZ"
    ]
    for fmt in potential_formats:
        try:
            return datetime.strptime(timestamp_string, fmt)
        except ValueError:
            continue
    return None
