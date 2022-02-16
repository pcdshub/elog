"""
Front-facing API for PCDS Elog
"""
import logging
import os
from collections import namedtuple
from configparser import ConfigParser, NoOptionError

from ophyd.status import StatusBase

from .pswww import PHPWebService
from .utils import facility_name, get_primary_elog, register_elog

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
    def __init__(self, logbooks, user=None, pw=None, base_url=None, dev=False):
        self.logbooks = logbooks
        self.service = PHPWebService(user=user, pw=pw,
                                     base_url=base_url, dev=dev
                                     )

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

    Usage:

        .. code-block:: python

            el = HutchELog('XPP')

            # Only 'tsd' currently works (2/22)
            el_dev = HutchELog('tsd', dev=True)

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

    primary : bool, optional
        If True, this will be the primary elog returned when the
        from_registry class method is used. If False, this will not be.
        If omitted, this will default to True if there is no primary elog
        or False if there already is one.
    """

    def __init__(self, instrument, station=None, user=None, pw=None,
                 base_url=None, primary=None, dev=False,
                 enable_run_posts=False):
        self.instrument = instrument
        self.station = station
        # Load an empty service
        logger.debug("Loading logbooks for %s", instrument)
        super().__init__({}, user=user, pw=pw, base_url=base_url, dev=dev)
        # Load the facilities logbook
        f_id = facility_name(instrument)
        self.logbooks['facility'] = self.service.get_facilities_logbook(f_id)
        # Load the experiment logbook
        exp_id = self.service.get_experiment_logbook(instrument,
                                                     station=station)
        self.logbooks['experiment'] = exp_id
        register_elog(self, primary=primary)

        # Switch for ELog posting callback in pcdshub/nabs
        self.enable_run_posts = enable_run_posts

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

    @classmethod
    def from_registry(cls):
        """
        Return the primary HutchElog object of the session.

        The first HutchElog created in the session will be the primary elog,
        unless another elog is created with the "primary=True" kwarg.
        There may be no primary elog at all if every single elog has been
        created with "primary=False", kwarg.

        This is for utilities that want to integrate with whatever the
        session's elog is without needing to pass around the elog as an
        argument to every bit of code that needs it.

        If no elog has been registered as the primary elog, this will raise a
        ValueError.
        """
        return get_primary_elog()

    def set(self, *args, **kwargs):
        """ Pass through method to post for Bluesky API compatibility """
        self.post(*args, **kwargs)

        # set message requrires a status object to be returned.
        # another message could possibly be used, but this seemed simplest
        status = StatusBase(done=True, success=True)
        return status
