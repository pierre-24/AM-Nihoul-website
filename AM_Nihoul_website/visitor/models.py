import os

import slugify
from sqlalchemy import event

from AM_Nihoul_website import db, uploads_set
from AM_Nihoul_website.base_models import BaseModel


class Category(BaseModel):
    name = db.Column(db.VARCHAR(length=150), nullable=False)

    @classmethod
    def create(cls, name):
        o = cls()
        o.name = name
        return o


class Page(BaseModel):
    """Page
    """

    title = db.Column(db.VARCHAR(length=150), nullable=False)
    slug = db.Column(db.VARCHAR(150), nullable=False)
    content = db.Column(db.Text)
    protected = db.Column(db.Boolean, default=False, nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category')

    @classmethod
    def create(cls, title, content, protected=False):
        o = cls()
        o.title = title
        o.content = content
        o.protected = protected

        return o


@event.listens_for(Page.title, 'set', named=True)
def receive_page_title_set(target, value, oldvalue, initiator):
    """Set the slug accordingly"""
    target.slug = slugify.slugify(value)


class UploadedFile(BaseModel):
    base_file_name = db.Column(db.VARCHAR(length=150), nullable=False)
    file_name = db.Column(db.VARCHAR(length=150), nullable=False)
    file_size = db.Column(db.Integer)
    possible_mime = db.Column(db.VARCHAR(length=150), nullable=False)
    description = db.Column(db.Text())

    @staticmethod
    def get_mimetype(path):
        """Get the mimetype of a file, using either libmagic or the mimetypes module when libmagic is not available."""
        if not os.path.exists(path):
            raise ValueError(path)

        try:
            import magic
            mime = magic.Magic(mime=True)
            return mime.from_file(path)
        except ImportError:
            import mimetypes
            mime = mimetypes.MimeTypes()
            return mime.guess_type(path)[0]

    @classmethod
    def create(cls, uploaded, filename, description=None):
        o = cls()
        o.base_file_name = uploaded.filename
        o.file_name = uploads_set.save(uploaded, name=filename)
        o.file_size = os.path.getsize(o.path())
        o.possible_mime = UploadedFile.get_mimetype(o.path())
        o.description = description

        return o

    def path(self):
        return uploads_set.path(self.file_name)

    def get_fa_icon(self):
        icons = {
            # documents
            'application/pdf': 'fas fa-file-pdf',
            'application/msword': 'fas fa-file-word',
            'application/vnd.ms-word': 'fas fa-file-word',
            'application/vnd.oasis.opendocument.text': 'fas fa-file-word',
            'application/vnd.openxmlformats-officedocument.wordprocessingml': 'fas fa-file-word',
            'application/vnd.ms-excel': 'fas fa-file-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml': 'fas fa-file-excel',
            'application/vnd.oasis.opendocument.spreadsheet': 'fas fa-file-excel',
            'application/vnd.ms-powerpoint': 'fas fa-file-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml': 'fas fa-file-powerpoint',
            'application/vnd.oasis.opendocument.presentation': 'fas fa-file-powerpoint',
            'text/plain': 'fas fa-file-alt',
            'text/html': 'fas fa-file-code',
            # archive
            'application/json': 'fas fa-file-code',
            'application/gzip': 'fas fa-file-archive',
            'application/zip': 'fas fa-file-archive',
            # images
            'image/png': 'fas fa-file-image',
            'image/jpeg': 'fas fa-file-image'
        }

        return icons[self.possible_mime] if self.possible_mime in icons else 'fas fa-file'

