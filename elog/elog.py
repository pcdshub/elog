"""
Front-facing API for PCDS Elog
"""
import logging
import os
from collections import namedtuple
from configparser import ConfigParser, NoOptionError

from .pswww import PHPWebService
from .utils import facility_name

logger = logging.getLogger(__name__)


Attachment = namedtuple('Attachment', ('path', 'description'))


class ELog:
    """
    Basic interface to ELog

    Parameters
    ----------
    logbooks : dict
        A mapping of aliases to logbook identifiers

    user : str, optional
        Username

    pw : str, optional
        Password, if this is left blank and a username is supplied the password
        will be requested via prompt

    base_url : str, optional
        Point to a different server; perhaps a test server.
    """
    def __init__(self, logbooks, user=None, pw=None, base_url=None):
        self.logbooks = logbooks
        self.service = PHPWebService(user=user, pw=pw, base_url=base_url)

    def post(self, msg, run=None, tags=None,
             attachments=None, logbooks=None, title=None):
        """
        Post to the logbooks

        Parameters
        ----------
        msg : str
            Desired text of LogBook message

        run : int, optional
            Associate the post with a specific run

        tags : list, optional
            List of tags to add to the post

        attachments : list, optional
            These can either be entered as the path to each attachment or a
            tuple of a path and description

        logbooks : list, optional
            Only post to a subset of the logbooks known by the client. If this
            is left as None, all logbooks will be included.

        title : str, optional
            Interprets the message as a HTML message with this as the title
        """
        logbooks = logbooks or self.logbooks.keys()
        for alias in logbooks:
            logger.info('Posting to %s logbook ...', alias)
            # Grab the information from our logbook
            try:
                book_id = self.logbooks[alias]
            except KeyError as exc:
                logger.exception('Invalid logbook name %s', exc)
            else:
                # Post the information to selected id
                self.service.post(msg, book_id,
                                  run=run, tags=tags,
                                  attachments=attachments,
                                  title=title)


class HutchELog(ELog):
    """
    ELog client for LCLS instruments

    This client will find the name of both the current experimental logbook as
    well as the facility logbook for the instrument. Authentication can be done
    in one of two ways; ws-auth if a username and/or password is supplied, or
    kerberos if these keywords are left blank

    Parameters
    ----------
    instrument : str
        Three letter acronym for instrument

    station : str, optional
        Specify a sub-station of the instrument

    user: str, optional
        Username for ws-auth authentication

    pw : str, optional
        Password, if this is left blank and a username is supplied the password
        will be requested via prompt

    base_url : str, optional
        Point to a different server; perhaps a test server.
    """
    def __init__(self, instrument, station=None, user=None, pw=None,
                 base_url=None):
        self.instrument = instrument
        self.station = station
        # Load an empty service
        logger.debug("Loading logbooks for %s", instrument)
        super().__init__({}, user=user, pw=pw, base_url=base_url)
        # Load the facilities logbook
        f_id = facility_name(instrument)
        self.logbooks['facility'] = self.service.get_facilities_logbook(f_id)
        # Load the experiment logbook
        exp_id = self.service.get_experiment_logbook(instrument,
                                                     station=station)
        self.logbooks['experiment'] = exp_id

    def post(self, msg, run=None, tags=None, attachments=None,
             experiment=True, facility=False, title=None):
        """
        Post to ELog

        Parameters
        ----------
        msg: str
            Body of message

        run : int, optional
            Associate the post with a specific run

        tags : list, optional
            List of tags to add to the post

        attachments : list, optional
            These can either be entered as the path to each attachment or a
            tuple of a path and description

        facility : bool, optional
            Post to the facility logbook

        experiment: bool, optional
            Post to the experimental logbook

        title : str, optional
            Interprets the message as a HTML message with this as the title
        """
        books = list()
        # Select our logbooks
        if experiment and facility:
            pass
        elif experiment:
            books.append('experiment')
        elif facility:
            books.append('facility')
        else:
            raise ValueError("Must select either facility or experiment")
        # Post
        super().post(msg, run=run, tags=tags,
                     attachments=attachments, logbooks=books, title=title)

    @classmethod
    def from_conf(cls, *args, **kwargs):
        """
        Load the login information from a stored configuration file

        A file ``web.cfg` is searched in the current directory or the user's
        home directory. The format of this configuration file is the standard
        ``.ini`` structure and should define the username and password like:

        .. code::

            [DEFAULT]
            user = MY_USERNAME
            pw = MY_PASSWORD
        """
        # Find the appropriate files
        cfg = ConfigParser()
        cfgs = cfg.read(['web.cfg', '.web.cfg',
                         os.path.expanduser('~/.web.cfg')])
        # Alert the user if we found no configuration files
        if not cfgs:
            raise EnvironmentError("No configuration file found")
        # Find the configuration
        try:
            user = cfg.get('DEFAULT', 'user')
            pw = cfg.get('DEFAULT', 'pw')
        except NoOptionError as exc:
            raise EnvironmentError('Must specify "user" and "pw" in '
                                   'configuration file') from exc
        # Return our device
        return cls(*args, user=user, pw=pw, **kwargs)
