"""
Interface for PHP based ELog web service
"""
import getpass
import logging
from urllib.parse import urlparse

import requests
from requests.auth import HTTPBasicAuth

from krtc import KerberosTicket


logger = logging.getLogger(__name__)


class PHPWebService:
    """
    PHP WebService Interface to ELog

    Authentication can be done in one of two ways, either the username or
    password can be entered directly or a valid KerberosTicket can be provided.
    The latter is assumed if no username is provided.

    Parameters
    ----------
    user : str, optional
        Username

    pw : str, optional
        Password. If not supplied, a prompt will launch requesting the
        password in a safe manner
    """
    base_url = 'https://pswww.slac.stanford.edu'

    def __init__(self, user=None, pw=None):
        self._auth = None
        self._url = None
        self.authenticate(user=user, pw=pw)

    def authenticate(self, user=None, pw=None):
        """
        Authorize use of the ELog

        If neither a username or password is supplied a Kerberos ticket will be
        used to authenticate the use of the ELog. Otherwise basic HTTPBasicAuth
        will be used.

        Parameters
        ----------
        user : str, optional
            Username

        pw : str, optional
            Password. If not supplied, a prompt will launch requesting the
            password in a safe manner

        Returns
        -------
        auth: dict
            Keywords necessary to properly authenticate a ``requests.get``
        """
        auth = dict()
        logger.debug("Creating authentication information ...")
        if user:
            # Create authentication URL and params for HTTP
            logger.debug("Using HTTP authorization ...")
            url = self.base_url + '/ws-auth'
            if not pw:
                pw = getpass.getpass()
            auth['auth'] = HTTPBasicAuth(user, pw)
        else:
            user = getpass.getuser()
            # Create authentication URL and params for Kerberos
            logger.debug("Using Kerberos ...")
            url = self.base_url + '/ws-kerb'
            host = urlparse(url).hostname
            auth['headers'] = KerberosTicket('HTTP@' + host).getAuthHeaders()
        # Store internal authentication information
        self._url = url
        self._auth = auth
        self._user = user
        return auth

    def get_facilities_logbook(self, instrument):
        """
        Gather Logbook information

        Parameters
        ----------
        instrument: str
            Name of the Instrument logbook

        Returns
        -------
        logbook_id : str
            ID of facilities logbook

        Example
        -------
        .. code:: python

            web.get_facilities_logbook('CXI Instrument')
        """
        # Format correct URL
        url = (self._url + '/LogBook/RequestExperimentsNew.php?instr=NEH'
               '&access=post&is_location')
        # Make request to WebService
        result = requests.get(url, **self._auth)
        # Invalid HTTP code
        if result.status_code >= 299:
            raise Exception('Failed to gather facilities information '
                            'from Web Service, HTTP status_code: {}'
                            ''.format(result.status_code))
        # Find the name that matches the specified instrument
        result = result.json()
        for book in result['ResultSet']['Result']:
            if book['name'] == instrument:
                return book['id']
        # If we never found our instrument
        raise Exception("Unable to find any Logbook for {}"
                        "".format(instrument))

    def get_experiment_logbook(self, instrument, station=None):
        """
        Gather information about the current experimental logbook

        Parameters
        ----------
        instrument : str
            Name of instrument

        station : str, optional
            Specify a specific station at the instrument

        Returns
        -------
        logbook_id: str
            ID of current experimental logbook

        Examples
        --------
        .. code:: python

            # Grabs active MFX experiment
            web.get_experiment_logbook('MFX')
            # Grabs active CXI secondary experiment
            web.get_experiment_logbook('CXI', station='1')
        """

        logger.debug("Requesting current experiment for %s", instrument)
        # Format correct URL
        url = '{url}/LogBook/RequestCurrentExperiment.php?instr={instr}'\
              ''.format(url=self._url, instr=instrument)
        if station:
            url += '&station={}'.format(station)
        # Make request to WebService
        result = requests.get(url, **self._auth)
        # Invalid HTTP code
        if result.status_code >= 299:
            raise Exception('Failed to gather current experiment information '
                            'from Web Service, HTTP status_code: {}'
                            ''.format(result.status_code))
        # Find experiment identification
        result = result.json()
        return result['ResultSet']['Result']['id']

    def post(self, msg, logbook_id,
             run=None, tags=None, attachments=None):
        """
        Post an entry to the ELog

        Parameters
        ----------
        msg : str
            Desired text of LogBook message

        logbook_id: str
            Three digit Identifier of Logbook

        run : int, optional
            Associate the post with a specific run

        tags : list, optional
            List of tags to add to the post

        attachments : list, optional
            These can either be entered as the path to each attachment or a
            tuple of a path and description
        """
        logger.debug("Posting to Logbook ID: %s", logbook_id)
        # Basic post information
        post = {'author_account': self._user,
                'message_text': msg,
                'id': logbook_id}
        # Convert tags
        if tags:
            post['num_tags'] = str(len(tags))
            for i, tag in enumerate(tags):
                post['tag_name_{}'.format(i)] = tag
                post['tag_value_{}'.format(i)] = ''
        # Convert our attachments
        files = dict()
        if attachments:
            for i, attachment in enumerate(attachments):
                # See if our attachment has a description
                if isinstance(attachment, str):
                    filename = attachment
                    description = attachment
                else:
                    (filename, description) = attachment
                # Format post information
                file_id = 'file{}'.format(i+1)
                files[file_id] = open(filename, 'rb')
                post[file_id] = description
        # Scope and Run information
        if run:
            post['scope'] = 'run'
            post['run_num'] = str(run)
        else:
            post['scope'] = 'experiment'
        # Make request to web service
        url = self._url + '/LogBook/NewFFEntry4grabberJSON.php'
        result = requests.post(url, data=post, files=files, **self._auth)
        # Invalid HTTP code
        if result.status_code >= 299:
            raise Exception('Failed to post information to Web Service. '
                            'HTTP status_code: {}'.format(result.status_code))
        # Convert to JSON
        result = result.json()
        if result['status'] != 'success':
            raise Exception('Failed to post information to Web Service. '
                            'Reason: {}'.format(result['Message']))
        else:
            logger.info('New message ID: %s', result['message_id'])
