"""
Utility functions for PCDS ELog
"""

primary_elog = None
registry = set()


def facility_name(hutch):
    """Return the facility name for an instrument"""
    if hutch in [
        'dia', 'mfx', 'mec', 'cxi', 'xcs', 'xpp', 'sxr', 'amo',
        'DIA', 'MFX', 'MEC', 'CXI', 'XCS', 'XPP', 'SXR', 'AMO',
    ]:
        return '{}_Instrument'.format(hutch.upper())
    return '{}_Instrument'.format(hutch.lower())


def get_primary_elog():
    """Return the registered primary elog"""
    if primary_elog is None:
        raise ValueError('No primary elog has been registered.')
    return primary_elog


def register_elog(elog, primary=None):
    """
    Register an elog to be retrieved later.

    All registered elogs will be added to the "registry" set.

    One elog at a time can be designated as the "primary" elog.
    Typically, this will be the main instrument elog associated
    with the hutch session.

    The "primary" elog can be quickly retrieved via get_primary_elog
    to be used in many places without needing to explicitly pass it
    around as an argument.

    Parameters
    ----------
    elog : Elog
        The elog to register.

    primary : bool, optional
        If True, this will be the primary elog returned when the
        get_primary_elog function called. If False, this will not be.
        If omitted, this will default to True if there is no primary elog
        or False if there already is one.
    """
    global primary_elog

    if primary is None:
        if primary_elog is None:
            primary = True
        else:
            primary = False

    if primary:
        primary_elog = elog

    registry.add(elog)


def clear_registry():
    """
    Reset the elog registry to the starting values.
    """
    global primary_elog
    primary_elog = None
    registry.clear()