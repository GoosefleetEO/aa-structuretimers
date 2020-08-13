# Structure Timers

An app for keeping track of Eve Online structure timers with Alliance Auth and Discord.

![release](https://img.shields.io/pypi/v/aa-timerboard?label=release) ![python](https://img.shields.io/pypi/pyversions/aa-timerboard) ![django](https://img.shields.io/pypi/djversions/aa-timerboard?label=django) ![pipeline](https://gitlab.com/ErikKalkoken/aa-timerboard/badges/master/pipeline.svg) ![coverage](https://gitlab.com/ErikKalkoken/aa-timerboard/badges/master/coverage.svg) ![license](https://img.shields.io/badge/license-MIT-green) ![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

## Contents

- [Overview](#overview)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Permissions](#permissions)
- [Management commands](#management-commands)

## Overview

Structure Timers is a rewrite of the Auth's timerboard app. On top of the basic functionality provided also by timerboard it has many additional useful features:

- Create and edit timers for structures
- See all current timers at a glance and with live countdowns for each
- Restrict access to your corporation members
- Get automatic notifications about upcoming timers on Discord
- Define a timer type (e.g. armor or hull)
- Restrict timer access to your alliance and/or people with opsec clearance
- Ability to add notes and a screenshot (e.g. with the structure's fitting) to a timer
- Create timers more quickly and precisely with autocomplete for solar system and structure types
- Find timers more quickly with category based filters and search
- Improved UI

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

1. Killtracker is a plugin for Alliance Auth. If you don't have Alliance Auth running already, please install it first before proceeding. (see the official [AA installation guide](https://allianceauth.readthedocs.io/en/latest/installation/auth/allianceauth/) for details)

2. Killtracker needs the app [django-eveuniverse](https://gitlab.com/ErikKalkoken/django-eveuniverse) to function. Please make sure it is installed, before before continuing.

Note that Timerboard is compatible with Auth's Structure Timer app and can be installed in parallel.

### Step 1 - Install app

Make sure you are in the virtual environment (venv) of your Alliance Auth installation. Then install the newest release from PyPI:

```bash
pip install aa-timerboard
```

### Step 2 - Configure settings

Configure your Auth settings (`local.py`) as follows:

- Add `'structuretimers'` to `INSTALLED_APPS`
- Add below lines to your settings file:

```python
CELERYBEAT_SCHEDULE['timerboard2_send_notifications'] = {
    'task': 'structuretimers.tasks.send_notifications',
    'schedule': crontab(minute='*/2'),
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

### Step 5 - Setup permission

Another important step is to setup permissions, to ensure the right people have access to Structure Timers. Please see [Permissions](#permissions) for an overview of all permissions.

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
