===============================================
Django Google API Python Client Storage Backend
===============================================

django-gapc-storage
-------------------

``django-gapc-storage`` is a Django storage backend for Google Cloud Storage
using the JSON API through google-api-python-client.


Requirements
--------------

* Django 1.8+

Settings
--------
Set the ``GCS_BUCKET`` environment variable to the GCS bucket to be used
by the storage backend.

Settings can be customized via the `GAPC_STORAGE` settings dict::

    GAPC_STORAGE = {
        "allow_overwrite": False,
        "bucket": "my-bucket",
        "cache_control": "public, max-age=3600",
        "num_retries": 0,
        "path_prefix": "",
    }


``GAPC_STORAGE["allow_overwrite"]``
===================================

Default: ``False``

If ``True``, the storage backend will overwrite an existing object with
the same name.

``GAPC_STORAGE["bucket"]``
==========================

Default: ``os.environ["GCS_BUCKET"]``

``GAPC_STORAGE["cache_control"]``
=================================

Default: ``public, max-age=3600``

By default, public-readable objects on GCS have a cache duration of 60
minutes.  Set ``cache_control`` to ``private, max-age=0`` to disable
public caching of objects saved by the storage backend.

``GAPC_STORAGE["num_retries"]``
===============================

Default: ``0``

Passed to the supported methods on the underlying google-api-python-client client which will retry 500 error responses with randomized exponential backoff.

For more information, see the [google-api-python-client documetation](http://google.github.io/google-api-python-client/docs/epy/googleapiclient.http.HttpRequest-class.html#execute

``GAPC_STORAGE["path_prefix"]``
===============================

Default: ``""``

A prefix appended to the path of objects saved by the storage backend.
For example, configuring path_prefix to ``media`` would save
objects to ``my-bucket/media``.
