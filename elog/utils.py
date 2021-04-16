"""
Utility functions for PCDS ELog
"""


def facility_name(hutch):
    """Return the facility name for an instrument"""
    if hutch in ['tmo', 'rix', 'txi', 'TMO', 'RIX', 'TXI']:
        return '{}_Instrument'.format(hutch.lower())
    return '{}_Instrument'.format(hutch.upper())
