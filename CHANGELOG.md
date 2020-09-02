# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - yyyy-mm-dd

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
