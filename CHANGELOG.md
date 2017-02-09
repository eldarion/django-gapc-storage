# Change Log

All notable changes to `django-gapc-storage` will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

## [0.3.1] - 2017-01-05

### Fixed

* calling open on a closed file will reopen the file ([#12](https://github.com/eldarion/django-gapc-storage/pull/12))

## [0.3.0] - 2016-12-20

### Added

* object Cache-Control metadata is now able to be overridden ([#7](https://github.com/eldarion/django-gapc-storage/pull/7))
* existing objects can now be overwritten on save ([#8](https://github.com/eldarion/django-gapc-storage/pull/8))
* documentation has been provided for settings ([#9](https://github.com/eldarion/django-gapc-storage/pull/9))

### Changed

* Backwards Incompatible: Changes in [#8](https://github.com/eldarion/django-gapc-storage/pull/8) require Django 1.8.  To continue using the project with Django<1.8, see a workaround documented in [#10](https://github.com/eldarion/django-gapc-storage/issues/10)

## [0.2.2] - 2016-12-14

### Fixed

* path_prefix is now applied correctly ([#6](https://github.com/eldarion/django-gapc-storage/pull/6))

## [0.2.1] - 2016-09-01

### Fixed

* GCS client is now thread safe
