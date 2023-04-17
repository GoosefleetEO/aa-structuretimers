# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## Unpublished

## [1.5.0] - tbd

### Added

- Localization

### Changes

- Minimum Python version increased to Python 3.8
- Added support for Python 3.10
- Switch to AA 3 and drop support for AA 2

## [1.4.2] - 2022-07-19

### Changed

- filterDropDown is bundled as template with AA >= 3.0.0b3 (!10)

## [1.4.1] - 2022-05-09

### Fixed

- Keep highlight in side bar navigation on edit page (!8)
- Translation tags fixed/added (!9)

## [1.4.0] - 2022-05-07

### Added

- Ability to specify dates directly when creating & editing timers (#15)

Thanks @colcrunch for your contribution!

## [1.3.1] - 2022-04-21

### Fixed

- Outdated dependency to django-eveuniverse

## [1.3.0] - 2022-04-19

### Added

- New timer clause for regions (#5)
- New timer clause for space type, i.e. high sec only (#26)

### Changed

- Some performace improvements for matching queries

## [1.2.4] - 2022-03-18

### Fixed

- Handle distance calculations for staging system object without solar system defined

## [1.2.3] - 2022-03-02

### Changed

- AA 3 compatibility update

## [1.2.2] - 2022-03-01

### Changed

- Improved Django 4 compatibility
- Updated dependencies to reflect current incompatibility with AA 3

## [1.2.1] - 2022-01-26

### Fixed

- Error: `MultipleObjectsReturned at /structuretimers/` when more then one staging system exists without an EveSolarSystem

## [1.2.0] - 2022-01-15

### Added

- Preliminary timers: Ability to create preliminary timers, which are timers without a date. This can be used for storing all infos about a structure including scanned fittings ahead of the initial attack. Preliminary timers are shown on a dedicated tab and can be converted to normal timers later simply by adding a date.

### Changed

- Improved logic when creating or editing timers:
  - When no date is specified, timers are automatically created as prelimiary.
  - When a partial date is entered, timers are create as normal timer and missing values are assumed to be zero. e.g. if you enter 5 for hours, then minutes and days are set to 0.
  - When you add a date to a preliminary date, it is upgrade to a normal (unspecified) timer.
- Removed support for Python 3.6 / Django 3.1

### Fixed

- Show distances for timers on all tabs
- Sort options for solar systems and types
- Sorting by distance

## [1.1.3] - 2021-11-12

### Fixed

- Fix: Housekeeping fails with exception without a timer to delete

## [1.1.2] - 2021-10-26

### Changed

- Update CI to include tests for both AA 2.8 with Py3.6/Dj31 and AA 2.9 with Py3.7+/Dj3.2

## [1.1.1] - 2021-07-14

### Fixed

- Wrong static file (#21)

## [1.1.0] - 2021-07-14

### Added

- Shows distance in ly and jumps from staging systems for timers
- Admins can define multple staging system and users can switch between them
- Users can copy existing timers to make it easier to create subsequent timers for the same structure (#20)
- Turned off setting the avatar for Discord webhooks (#14)

### Changed

- Removed creator column
- Removed timers from admin site
- Minor UI improvements for edit and delete pages

### Fixed

- Restrict creating moon mining timers to refineries (#17)

## 1.0.7 - 2021-05-05

### Fixed

- Reduced load time for timers list
- Buttons no longer wrapping

## 1.0.6 - 2021-04-13

### Changed

- Add isort to CI

### Fixed

- Shows wrong page count on timers list
- Too long owner names result in 2-lines filter row

## 1.0.5 - 2021-03-07

### Changed

- Migrated to allianceauth-app-utils
- Migrated to extensions logger

### Fixed

- Fix attempt: Structuretimers sometimes get stuck [#19](https://gitlab.com/ErikKalkoken/aa-structuretimers/-/issues/19)

## 1.0.4 - 2021-01-29

### Changed

- Integration with codecov
- Pre-commit

### Fixed

- Error 500 when Structure Type remains empty [#16](https://gitlab.com/ErikKalkoken/aa-structuretimers/-/issues/16)

## 1.0.3 - 2020-10-24

### Changed

- Improved styling
- Updated test matrix

## 1.0.2 - 2020-09-22

### Changed

- Removed dependency conflict with Auth regarding Django 3

## 1.0.1 - 2020-09-16

**Updating notes**

After completing the normal update steps please also rerun the following management command to get the new types:

```bash
python manage.py structuretimers_load_eve
```

### Fixed

- It is now possible to create new timers for TCUs and I-Hubs

## 1.0.0 - 2020-09-15

### Fixed

- Formatting fix for sidebar

Thank you Exiom for the contribution.

## 1.0.0b6 - 2020-09-10

**Updating notes**

After completing the normal update steps please also rerun the following management command to get the new types:

```bash
python manage.py structuretimers_load_eve
```

### Added

- Mobile Depots added as new structure type [#10](https://gitlab.com/ErikKalkoken/aa-structuretimers/-/issues/10)

### Changed

- Moved JS/CSS vendor packages locally to comply with GDPR [#9](https://gitlab.com/ErikKalkoken/aa-structuretimers/-/issues/9)

### Fixed

- List of timers automatically scrolls to end of page if page is larger than the screen

## 1.0.0b5 - 2020-09-01

### Added

- Now validates that the details image URL points to a valid image file [#7](https://gitlab.com/ErikKalkoken/aa-structuretimers/-/issues/7)

### Changed

- Upgrade to new Black version

### Fixed

- List of timers automatically resets to first page every second [#8](https://gitlab.com/ErikKalkoken/aa-structuretimers/-/issues/8)

## 1.0.0b4 - 2020-08-26

### Changed

- Added additional protection against notification duplicates [#3](https://gitlab.com/ErikKalkoken/aa-structuretimers/-/issues/3)

## 1.0.0b3 - 2020-08-25

### Added

- Local time now shown along eve time in timer list

### Fixed

- Form validation no longer forgets values for structure and solar system [#1](https://gitlab.com/ErikKalkoken/aa-structuretimers/-/issues/1)
- Users can delete their own timers
- Will no longer upgrade to Django 3

## 1.0.0b2 - 2020-08-19

### Fixed

- Attempt to fix occasional multi-sending of notifications
- No shows corporation name of creator for generated timers
- Now using full width of webpage for timers list

## 1.0.0b1 - 2020-08-16

Initial release
