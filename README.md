<h1 align="center">ELog</h1>

<div align="center">
  <!-- Build Status -->
  <a href="https://travis-ci.org/pcdshub/elog">
    <img
src="https://img.shields.io/travis/pcdshub/elog/master.svg?style=flat-square"
      alt="Build Status" />
  </a>
</div>

<div align="center">
  <strong>Python API to the Photon Experimental ELog</strong>
</div>

<p align="center">
  <a href="#motivation">Installation</a> •
  <a href="#features">Basic Usage</a> •
  <a href="#installation">Authentication</a> •
  <a href="#installation">Test Suite</a> •
</p>


## Installation
The `elog` package is available on both the `pcds-tag` and `pcds-dev` conda
channels. Quick installation looks like:

```shell
conda install elog -c pcds-tag`
```

## Basic Usage
The most common use case for the ELog is to interface with the current
experiment logbook and facilities logbook for a given endstation. If this is
your use case, the `HutchELog` handles finding both of these automatically.
Otherwise, you can manually enter the Logbook id in the base `ELog` class.

```python
   import elog
   mfx_elog = elog.HutchELog('MFX')
```

Use the post method to add messages to the `pswwww` site with any additional
tags and attachments you may need. By default, the experiment logbook is posted
to, but the facility logbook is not, simply adjust this by using the `facility`
and `experiment` keywords:

```python
   # Post a message to the experiment logbook
   mfx_elog.post('This is experiment information', tags=['sample'])
   # Post a message to both logbooks
   mfx_elog.post('Important: Everyone please read', facility=True)
   # Post a message to only the facility logbook
   mfx_elog.post('Note for controls staff', tags=['bug_report'],
                 attachments=[('path/to/log.txt', 'Relevant log file')])
```
   
## Authentication
Most users will authenticate with `kerberos` this is the assumption made if no
username or password is passed into the class constructor. However, for
certain accounts password authentication is needed. Four examples of different
authentication methods are shown below

```python
   # Kerberos ticket is used for authentication
   elog.ELog()
   # Log-in as user but request the password via command line
   elog.ELog(user='user')
   # Log-in as user directly
   elog.ELog(user='user', pw='not_my_pw')
   # Search for a configuration file that contains username and password
   elog.ELog.from_conf()
```

## Test Suite
The automated testing package will attempt to actually interface with the web
server using `kerberos` authentication. If you do not want to run these tests
you can use the keyword `no-kerberos` to skip the relevant tests and run with a
different username and password.

```shell
python run_tests --user my_user --pw my_pw --no-kerberos
```

There are also tests that post to the web service but these are disabled by
default. If you think you need to run these in order to check changes you have
made to the repository use `--post`.
