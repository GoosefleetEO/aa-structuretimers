# Timerboard

An app for keeping track of structure timers

![release](https://img.shields.io/pypi/v/aa-timerboard?label=release) ![python](https://img.shields.io/pypi/pyversions/aa-timerboard) ![django](https://img.shields.io/pypi/djversions/aa-timerboard?label=django) ![pipeline](https://gitlab.com/ErikKalkoken/aa-timerboard/badges/master/pipeline.svg) ![coverage](https://gitlab.com/ErikKalkoken/aa-timerboard/badges/master/coverage.svg) ![license](https://img.shields.io/badge/license-MIT-green) ![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

## Contents

- [Overview](#overview)
- [Installation](#installation)
- [Management commands](#management-commands)

## Overview

Timerboard2 is an enhancement of the Auth timerboard / structure timers app. It has the same basic functionality has timerboard:

- Create and edit timers for structures
- See all current timers at a glance and with live countdowns for each
- Restrict access to your corporation members

But also comes with many of the additional features that have been requested by users for years:

- Restrict access to your alliance and/or people with opsec clearance
- Define a timer type (e.g. armor or hull)
- Ability to add notes and a screenshot (e.g. with the structure's fitting) to a timer
- Create timers more quickly and precisely with autocomplete for solar system and structure types
- Find timers more quickly with category based filters and search
- Improved UI

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

- Add `'timerboard2'` to `INSTALLED_APPS`
- Add below lines to your settings file:

```python
CELERYBEAT_SCHEDULE['timerboard2_run_killtracker'] = {
    'task': 'timerboard2.tasks.run_killtracker',
    'schedule': crontab(minute='*/1'),
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
python manage.py timerboard_load_eve
```

You may want to wait until the data loading is complete before starting to create new timers.

## Management commands

The following management commands are available:

- **timerboard_load_eve**: Preload all eve objects required for this app to function
