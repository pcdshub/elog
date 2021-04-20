"""
Utility functions for PCDS ELog
"""


def facility_name(hutch):
    """Return the facility name for an instrument"""
    if hutch in [
        'dia', 'mfx', 'mec', 'cxi', 'xcs', 'xpp', 'sxr', 'amo',
        'DIA', 'MFX', 'MEC', 'CXI', 'XCS', 'XPP', 'SXR', 'AMO',
    ]:
        return '{}_Instrument'.format(hutch.upper())
    return '{}_Instrument'.format(hutch.lower())
