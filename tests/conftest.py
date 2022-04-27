import getpass

import pytest

from elog.pswww import PHPWebService


def pytest_addoption(parser):
    parser.addoption('--user', action='store', default=None,
                     help='Username for ws-auth authentication')
    parser.addoption('--pw', action='store', default=None,
                     help='Password user for ws-auth authentication')
    parser.addoption('--kerberos', action='store_true', default=False,
                     help='Whether or not to attempt Kerberos authentication')
    parser.addoption('--post', action='store_true', default=False,
                     help='Whether to include tests that post to the ELog')


def pytest_generate_tests(metafunc):
    # Create a ws-kerb webservice
    services = []
    ids = []
    # Create a Kerberos authentication
    if metafunc.config.option.kerberos:
        services.append(PHPWebService())
        ids.append('ws-kerb')

    # Create our ws-auth webservice if a username was provided
    if metafunc.config.option.user:
        # Request a password if None was given
        if not metafunc.config.option.pw:
            metafunc.config.option.pw = getpass.getpass()
        # Create our ws-auth webservice
        services.append(PHPWebService(metafunc.config.option.user,
                                      metafunc.config.option.pw))
        ids.append('ws-auth')
    # Pass our services on to tests
    if 'pswww' in metafunc.fixturenames:
        metafunc.parametrize("pswww", services, ids=ids)


def pytest_collection_modifyitems(config, items):
    # Otherwise skip posting tests
    skip_post = pytest.mark.skip(reason='Instructed not to post to ELog')
    for item in items:
        if 'post' in item.keywords and not config.getoption('--post'):
            item.add_marker(skip_post)
