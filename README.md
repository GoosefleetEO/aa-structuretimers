# Structure Timers II

An app for keeping track of Eve Online structure timers with Alliance Auth and Discord.

![release](https://img.shields.io/pypi/v/aa-structuretimers?label=release) ![python](https://img.shields.io/pypi/pyversions/aa-structuretimers) ![django](https://img.shields.io/pypi/djversions/aa-structuretimers?label=django) ![pipeline](https://gitlab.com/ErikKalkoken/aa-structuretimers/badges/master/pipeline.svg) ![coverage](https://gitlab.com/ErikKalkoken/aa-structuretimers/badges/master/coverage.svg) ![license](https://img.shields.io/badge/license-MIT-green) ![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

## Contents

- [Overview](#overview)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Settings](#settings)
- [Permissions](#permissions)
- [Management commands](#management-commands)

## Overview

*Structure Timers II* is an enhanced version of the Alliance Auth's Structure Timers app, with many additional useful features and an improved UI. Here is a overview of it's main features in comparison to Auth's basic variant.

Feature | Auth | Structure Timer II
--|--|--
Create and edit timers for structures | x | x
See all pending timers at a glance and with live countdowns | x | x
Restrict timer access to your corporation | x | x
Restrict ability to create and delete timers to certain users | x | x
Get automatic notifications about upcoming timers on Discord  | - | x
Define a timer type (e.g. armor or hull)| - | x
Restrict timer access to your alliance | - | x
Restrict timer access to people with special clearance ("OPSEC") | - | x
Add screenshots to timers (e.g. with the structure's fitting)| - | x
Create timers more quickly and precisely with autocomplete for solar system and structure types| - | x
Find timers more quickly with filters and full text search | - | x
Automatic cleanup of elapsed timers | - | x

## Screenshots

### List of timers

![timerboard](https://i.imgur.com/LXsvyvY.png)

### Details for a timer

![timerboard](https://i.imgur.com/ZEbl2Vc.png)

### Creating a new timer

![timerboard](https://i.imgur.com/LPCEQNr.png)

### Notification on Discord

![notification](https://i.imgur.com/X0t5Kuj.png)

## Installation

### Preconditions

1. Structure Timers is a plugin for Alliance Auth. If you don't have Alliance Auth running already, please install it first before proceeding. (see the official [AA installation guide](https://allianceauth.readthedocs.io/en/latest/installation/auth/allianceauth/) for details)

2. Structure Timers needs the app [django-eveuniverse](https://gitlab.com/ErikKalkoken/django-eveuniverse) to function. Please make sure it is installed, before before continuing.

Note that Structure Timers is compatible with Auth's Structure Timer app and can be installed in parallel.

### Step 1 - Install app

Make sure you are in the virtual environment (venv) of your Alliance Auth installation. Then install the newest release from PyPI:

```bash
pip install aa-structuretimers
```

### Step 2 - Configure settings

Configure your Auth settings (`local.py`) as follows:

- Add `'structuretimers'` to `INSTALLED_APPS`
- Add the following lines to your settings file:

```python
CELERYBEAT_SCHEDULE['structuretimers_housekeeping'] = {
    'task': 'structuretimers.tasks.housekeeping',
    'schedule': crontab(minute=0, hour=3),
}
```

- Optional: Add additional settings if you want to change any defaults. See [Settings](#settings) for the full list.

### Step 3 - Finalize installation

Run migrations & copy static files

```bash
python manage.py migrate
python manage.py collectstatic
```

Restart your supervisor services for Auth

### Step 4 - Preload Eve Universe data

In order to be able to select solar systems and structure types for timers you need to preload some data from ESI once. If you already have run those commands previously you can skip this step.

Load Eve Online map:

```bash
python manage.py eveuniverse_load_data map
```

```bash
python manage.py structuretimers_load_eve
```

You may want to wait until the data loading is complete before starting to create new timers.

### Step 5 - Setup permissions

Another important step is to setup permissions, to ensure the right people have access features. Please see [Permissions](#permissions) for an overview of all permissions.

### Step 6 - Migrate existing timers

Last, but not least: If you have already been using the classic Structure Timers app from Auth, you can migrate your existing timers over to new app. Just run the following command:

```bash
python manage.py structuretimers_migrate_timers
```

## Settings

Here is a list of available settings for this app. They can be configured by adding them to your Auth settings file (`local.py`).

Note that all settings are optional and the app will use the documented default settings if they are not used.

Name | Description | Default
-- | -- | --
`TIMERBOARD2_MAX_AGE_FOR_NOTIFICATIONS`| Will not sent notifications for timers, which event time is older than the given minutes | `60`
`TIMERBOARD2_NOTIFICATIONS_ENABLED`| Wether notifications for timers are scheduled at all | `True`
`TIMERBOARD2_TIMERS_OBSOLETE_AFTER_DAYS`| Minimum age in days for a timer to be considered obsolete. Obsolete timers will automatically be deleted. If you want to keep all timers, set to `None` | `30`

## Permissions

Here are all relevant permissions:

Codename | Description
-- | --
`general - Can access this app and see timers` | Basic permission required by anyone to access this app. Gives access to the list of timers (which timers a user sees can depend on other permissions and settings for a timers)
`general - Can create new timers and edit own timers` | Users with this permission can create new timers and their own timers.
`general - Can edit and delete any timer` | Users with this permission can edit and delete any timer.
`general - Can create and see opsec timers` | Users with this permission can create and view timers that are opsec restricted.

## Management commands

The following management commands are available:

- **structuretimers_load_eve**: Preload all eve objects required for this app to function
- **structuretimers_migrate_timers**: Migrate pending timers from Auth's Structure Timers apps
