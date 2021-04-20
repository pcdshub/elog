import os
import pytest

import elog.elog
from elog.elog import HutchELog
from elog.utils import clear_registry, registry


@pytest.fixture(scope='module')
def patch_webservice():
    # A very basic mock Webservice
    class WebService:

        def __init__(self, *args, **kwargs):
            self.posts = list()

        def post(self, *args, **kwargs):
            self.posts.append((args, kwargs))

        def get_facilities_logbook(self, instrument):
            return '0'

        def get_experiment_logbook(self, instrument, station=None):
            return '1'

    # Store value
    orig_web = elog.elog.PHPWebService
    elog.elog.PHPWebService = WebService
    yield
    elog.elog.PHPWebService = orig_web


@pytest.fixture(scope='module')
def mockelog(patch_webservice):
    yield HutchELog('TST')


@pytest.fixture(scope='function')
def temporary_config():
    cfg = """\
    [DEFAULT]
    user=user
    pw=pw
    """
    with open('web.cfg', '+w') as f:
        f.write(cfg)
    # Allow the test to run
    yield
    # Remove the file
    os.remove('web.cfg')


def test_hutchelog_init(mockelog):
    assert mockelog.logbooks['facility'] == '0'
    assert mockelog.logbooks['experiment'] == '1'


def test_elog_post(mockelog):
    mockelog.post('Both logbooks', tags='first', facility=True)
    assert len(mockelog.service.posts) == 2
    mockelog.post('Facility', experiment=False, facility=True)
    assert len(mockelog.service.posts) == 3
    assert mockelog.service.posts[-1][0][1] == '0'
    mockelog.post('Experiment')
    assert len(mockelog.service.posts) == 4
    assert mockelog.service.posts[-1][0][1] == '1'
    with pytest.raises(ValueError):
        mockelog.post('Failure', experiment=False, facility=False)


def test_elog_from_conf(temporary_config):
    # Fake ELog that stores the username and pw internally
    class TestELog(HutchELog):

        def __init__(self, instrument, user=None, pw=None):
            self.instrument = instrument
            self.user = user
            self.pw = pw

    log = TestELog.from_conf('TST')
    assert log.instrument == 'TST'
    assert log.user == 'user'
    assert log.pw == 'pw'


def test_elog_from_registry(patch_webservice):
    clear_registry()
    with pytest.raises(ValueError):
        HutchELog.from_registry()
    elog0 = HutchELog('TST', primary=False)
    with pytest.raises(ValueError):
        HutchELog.from_registry()
    elog1 = HutchELog('TST')
    assert HutchELog.from_registry() is elog1
    elog2 = HutchELog('TST')
    assert HutchELog.from_registry() is elog1
    elog3 = HutchELog('TST', primary=True)
    assert HutchELog.from_registry() is elog3
    for elog in (elog0, elog1, elog2, elog3):
        assert elog in registry
