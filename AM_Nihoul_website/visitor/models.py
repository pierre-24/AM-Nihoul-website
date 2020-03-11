import os

import slugify
from sqlalchemy import event

from AM_Nihoul_website import db, uploads_set
from AM_Nihoul_website.base_models import BaseModel


class Category(BaseModel):
    name = db.Column(db.VARCHAR(length=150), nullable=False)
    order = db.Column(db.Integer, nullable=False)

    @classmethod
    def create(cls, name):
        o = cls()
        o.name = name

        # set order
        last_c = Category.query.order_by(Category.order.desc()).first()
        o.order = last_c.order + 1 if last_c else 0

        return o

    def __str__(self):
        return 'Catégorie {} ({})'.format(self.id, self.name)

    def _move(self, offset):
        if offset == 0:
            return
        if self.id is None:
            raise Exception('should get an id first')

        categories = Category.query.order_by(Category.order).all()

        # find self
        _self = -1
        for i, c in enumerate(categories):
            if c.id == self.id:
                _self = i
                break

        if _self == -1:
            raise Exception('cannot find self !?')

        # compute new position
        final_position = _self + offset
        if final_position < 0:
            final_position = 0
        if final_position >= len(categories):
            final_position = len(categories) - 1
        if final_position == _self:
            return

        # change everyone's order:
        self.order = final_position
        db.session.add(self)

        minimum = (_self + 1) if _self < final_position else final_position
        for i in range(minimum, minimum + abs(offset)):
            categories[i].order += 1 if offset < 0 else -1
            db.session.add(categories[i])

        db.session.commit()

    def up(self):
        self._move(1)

    def down(self):
        self._move(-1)


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
    def create(cls, title, content, protected=False, category_id=None):
        o = cls()
        o.title = title
        o.content = content
        o.protected = protected
        o.category_id = category_id

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
