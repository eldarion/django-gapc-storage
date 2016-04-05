import io
import mimetypes
import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import Storage
from django.utils.functional import SimpleLazyObject
from django.utils.http import urlquote

import dateutil.parser
import httplib2

from googleapiclient.discovery import build as discovery_build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from oauth2client.client import GoogleCredentials


def _gcs_file_storage_settings():
    config = getattr(settings, "GAPC_STORAGE", {})

    def default_bucket():
        try:
            return os.environ["GCS_BUCKET"]
        except KeyError:
            raise ImproperlyConfigured("Either GAPC_STORAGE[bucket] or env var GCS_BUCKET need to be set.")
    config.setdefault("bucket", SimpleLazyObject(default_bucket))

    return config


class GoogleCloudStorage(Storage):
    """
    Django storage backend for Google Cloud Storage (GCS)

    This storage backend uses google-api-python-client to interact with GCS. It
    makes no assumptions about your environment and can be used anywhere.
    """

    def __init__(self):
        self.set_client()
        self.bucket = _gcs_file_storage_settings()["bucket"]

    def set_client(self):
        credentials = self.get_oauth_credentials()
        http = credentials.authorize(httplib2.Http())
        self.client = discovery_build("storage", "v1", http=http)

    def get_oauth_credentials(self):
        return self.create_scoped(GoogleCredentials.get_application_default())

    def create_scoped(self, credentials):
        return credentials.create_scoped(["https://www.googleapis.com/auth/devstorage.read_write"])

    def get_gcs_object(self, name):
        req = self.client.objects().get(bucket=self.bucket, object=name)
        try:
            return req.execute()
        except HttpError as exc:
            if exc.resp["status"] == "404":
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
        req = self.client.objects().get_media(bucket=self.bucket, object=name)
        buf = self._open_io()
        media = MediaIoBaseDownload(buf, req)
        done = False
        while not done:
            done = media.next_chunk()[1]
        buf.seek(0)
        return buf

    def _save(self, name, content):
        mimetype, _ = mimetypes.guess_type(os.path.basename(name))
        if mimetype is None:
            mimetype = "application/octet-stream"
        media = MediaIoBaseUpload(content, mimetype)
        req = self.client.objects().insert(bucket=self.bucket, name=name, media_body=media)
        req.execute()
        return name

    def delete(self, name):
        req = self.client.objects().delete(bucket=self.bucket, object=name)
        try:
            return req.execute()
        except HttpError as exc:
            if exc.resp["status"] == "404":
                return
            raise

    def exists(self, name):
        return self.get_gcs_object(name) is not None

    def size(self, name):
        return int(self.get_gcs_object(name)["size"])

    def url(self, name):
        url_template = _gcs_file_storage_settings().get(
            "url-template",
            "https://storage.googleapis.com/{bucket}/{name}"
        )
        url = url_template.format(bucket=self.bucket, name=name)
        scheme, rest = url.split("://")
        return "{}://{}".format(scheme, urlquote(rest))

    def created_time(self, name):
        return dateutil.parser.parse(self.get_gcs_object(name)["timeCreated"])

    def modified_time(self, name):
        return dateutil.parser.parse(self.get_gcs_object(name)["updated"])
