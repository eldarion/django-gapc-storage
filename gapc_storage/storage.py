import io
import mimetypes
import os
import threading

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import Storage
from django.utils.encoding import force_text
from django.utils.functional import SimpleLazyObject
from django.utils.http import urlquote
from django.utils.six.moves.urllib import parse as urlparse

import dateutil.parser
import httplib2

from googleapiclient.discovery import build as discovery_build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from oauth2client.client import GoogleCredentials


GCS_PUBLIC_READ_CACHE_DEFAULT = "public, max-age=3600"
GCS_PUBLIC_READ_CACHE_DISABLED = "private, max-age=0"


def safe_join(base, *paths):
    """
    A version of django.utils._os.safe_join for GCS paths.
    Joins one or more path components to the base path component
    intelligently. Returns a normalized version of the final path.
    The final path must be located inside of the base path component
    (otherwise a ValueError is raised).
    Paths outside the base path indicate a possible security
    sensitive operation.

    Adapted from django-storages.
    """
    base_path = force_text(base)
    base_path = base_path.rstrip("/")
    paths = [force_text(p) for p in paths]

    final_path = base_path
    for path in paths:
        final_path = urlparse.urljoin(final_path.rstrip("/") + "/", path)

    # Ensure final_path starts with base_path and that the next character after
    # the final path is "/" (or nothing, in which case final_path must be
    # equal to base_path).
    base_path_len = len(base_path)
    if (not final_path.startswith(base_path) or
            final_path[base_path_len:base_path_len + 1] not in ("", "/")):
        raise ValueError("the joined path is located outside of the base path"
                         " component")

    return final_path.lstrip("/")


def _gcs_file_storage_settings():
    config = getattr(settings, "GAPC_STORAGE", {})

    def default_bucket():
        try:
            return os.environ["GCS_BUCKET"]
        except KeyError:
            raise ImproperlyConfigured("Either GAPC_STORAGE[bucket] or env var GCS_BUCKET need to be set.")
    config.setdefault("bucket", SimpleLazyObject(default_bucket))

    config.setdefault("path_prefix", "")
    config.setdefault("allow_overwrite", False)
    config.setdefault("cache_control", GCS_PUBLIC_READ_CACHE_DEFAULT)

    return config


class GoogleCloudStorage(Storage):
    """
    Django storage backend for Google Cloud Storage (GCS)

    This storage backend uses google-api-python-client to interact with GCS. It
    makes no assumptions about your environment and can be used anywhere.
    """

    def __init__(self):
        self.thread = threading.local()
        config = _gcs_file_storage_settings()
        self.bucket = config["bucket"]
        self.path_prefix = self.path_prefix if hasattr(self, "path_prefix") else config["path_prefix"]
        self.allow_overwrite = self.allow_overwrite if hasattr(self, "allow_overwrite") else config["allow_overwrite"]
        self.cache_control = self.cache_control if hasattr(self, "cache_control") else config["cache_control"]

    def build_client(self):
        credentials = self.get_oauth_credentials()
        http = credentials.authorize(httplib2.Http())
        return discovery_build("storage", "v1", http=http)

    @property
    def client(self):
        if not hasattr(self.thread, "client"):
            self.thread.client = self.build_client()
        return self.thread.client

    def get_oauth_credentials(self):
        return self.create_scoped(GoogleCredentials.get_application_default())

    def create_scoped(self, credentials):
        return credentials.create_scoped(["https://www.googleapis.com/auth/devstorage.read_write"])

    def _prefixed_name(self, name):
        """
        Append an optional prefix to objects to allow sub-directories
        within GCS buckets.

        Useful for using a single bucket for static and media assets.
        """
        return safe_join(self.path_prefix, name)

    def get_gcs_object(self, name, ensure=True):
        req = self.client.objects().get(bucket=self.bucket, object=self._prefixed_name(name))
        try:
            return req.execute()
        except HttpError as exc:
            if exc.resp["status"] == "404":
                if ensure:
                    raise IOError('object "{}/{}" does not exist'.format(self.bucket, self._prefixed_name(name)))
                else:
                    return None
            raise

    def _open_io(self):
        """
        io.IOBase instance to use for reading files from GCS.
        """
        # default IO is in-memory (not ideal, but works great for small files)
        return io.BytesIO()

    # Django Storage interface

    def _open(self, name, mode):
        if mode != "rb":
            raise ValueError("rb is the only acceptable mode for this backend")
        req = self.client.objects().get_media(bucket=self.bucket, object=self._prefixed_name(name))
        buf = self._open_io()
        media = MediaIoBaseDownload(buf, req)
        done = False
        try:
            while not done:
                done = media.next_chunk()[1]
        except HttpError as exc:
            if exc.resp["status"] == "404":
                raise IOError('object "{}/{}" does not exist'.format(self.bucket, self._prefixed_name(name)))
            else:
                raise IOError("unknown HTTP error: {}".format(exc))
        buf.seek(0)
        return buf

    def _save(self, name, content):
        mimetype, _ = mimetypes.guess_type(os.path.basename(name))
        if mimetype is None:
            mimetype = "application/octet-stream"
        media = MediaIoBaseUpload(content, mimetype)
        req = self.client.objects().insert(
            bucket=self.bucket,
            name=self._prefixed_name(name),
            body={
                "cacheControl": self.cache_control
            },
            media_body=media
        )
        req.execute()
        return name

    def delete(self, name):
        req = self.client.objects().delete(bucket=self.bucket, object=self._prefixed_name(name))
        try:
            return req.execute()
        except HttpError as exc:
            if exc.resp["status"] == "404":
                return
            raise

    def exists(self, name):
        return self.get_gcs_object(name, ensure=False) is not None

    def size(self, name):
        return int(self.get_gcs_object(name)["size"])

    def url(self, name):
        url_template = _gcs_file_storage_settings().get(
            "url-template",
            "https://storage.googleapis.com/{bucket}/{name}"
        )
        url = url_template.format(bucket=self.bucket, name=self._prefixed_name(name))
        scheme, rest = url.split("://")
        return "{}://{}".format(scheme, urlquote(rest))

    def created_time(self, name):
        return dateutil.parser.parse(self.get_gcs_object(name)["timeCreated"])

    def modified_time(self, name):
        return dateutil.parser.parse(self.get_gcs_object(name)["updated"])

    def get_available_name(self, name, max_length=None):
        if self.allow_overwrite:
            return name
        return super(GoogleCloudStorage, self).get_available_name(name, max_length)
