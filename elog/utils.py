"""
Utility functions for PCDS ELog
"""


def facility_name(hutch):
    """Return the facility name for an instrument"""
    return '{}_Instrument'.format(hutch.upper())
