# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

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
