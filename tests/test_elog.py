import os

import pytest

import elog.elog


@pytest.fixture(scope='module')
def mockelog():

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
    yield elog.elog.HutchELog('TST')
    elog.elog.PHPWebService = orig_web


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
    class TestELog(elog.elog.HutchELog):

        def __init__(self, instrument, user=None, pw=None):
            self.instrument = instrument
            self.user = user
            self.pw = pw

    log = TestELog.from_conf('TST')
    assert log.instrument == 'TST'
    assert log.user == 'user'
    assert log.pw == 'pw'
