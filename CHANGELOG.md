# Change Log

## 0.3.0
* added the ability to override object Cache-Control metadata ([#7](https://github.com/eldarion/django-gapc-storage/pull/7))
* added the ability to overwrite an existing object on save ([#8](https://github.com/eldarion/django-gapc-storage/pull/8))
* documented available settings ([#9](https://github.com/eldarion/django-gapc-storage/pull/9))
* Backwards Incompatible: Changes in [#8](https://github.com/eldarion/django-gapc-storage/pull/8) require Django 1.8.  To continue using the project with Django<1.8, see a workaround documented in [#10](https://github.com/eldarion/django-gapc-storage/issues/10)

## 0.2.2
* fixed bug where path_prefix was applied incorrectly ([#6](https://github.com/eldarion/django-gapc-storage/pull/6))

## 0.2.1

* fixed thread safety issue with GCS client
