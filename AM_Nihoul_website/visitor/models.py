import os
import secrets
import slugify
import datetime

from sqlalchemy import event

from AM_Nihoul_website import db, uploads_set
from AM_Nihoul_website.base_models import BaseModel


class OrderableMixin:
    """An object that can be ordered in any order"""

    order = db.Column(db.Integer, nullable=False, default=0)

    @classmethod
    def ordered_items(cls, desc=False, **kwargs):
        """Should return the list of objects, ordered by ``order``.
        """

        if desc:
            return cls.query.order_by(cls.order.desc())
        else:
            return cls.query.order_by(cls.order)

    def _move(self, offset, **kwargs):
        if offset == 0:
            return
        if self.id is None:
            raise Exception('should get an id first')

        ordered_items = self.ordered_items(desc=False, **kwargs).all()

        # find self
        _self = -1
        for i, c in enumerate(ordered_items):
            if c.id == self.id:
                _self = i
                break

        if _self == -1:
            raise Exception('cannot find self !?')

        # compute new position
        final_position = _self + offset
        if final_position < 0:
            final_position = 0
        if final_position >= len(ordered_items):
            final_position = len(ordered_items) - 1
        if final_position == _self:
            return

        # change everyone's order:
        self.order = final_position
        db.session.add(self)

        minimum = (_self + 1) if _self < final_position else final_position
        for i in range(minimum, minimum + abs(offset)):
            ordered_items[i].order += 1 if offset < 0 else -1
            db.session.add(ordered_items[i])

        db.session.commit()

    def up(self, **kwargs):
        """Increase current order"""
        self._move(1, **kwargs)

    def down(self, **kwargs):
        """Decrease current order"""
        self._move(-1, **kwargs)


class Category(OrderableMixin, BaseModel):
    """Category (of the pages)"""

    name = db.Column(db.VARCHAR(length=150), nullable=False)

    @classmethod
    def create(cls, name):
        o = cls()
        o.name = name

        # set order
        last_c = Category.ordered_items(desc=True).first()
        o.order = last_c.order + 1 if last_c else 0

        return o

    def __str__(self):
        return 'Catégorie {} ({})'.format(self.id, self.name)


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


@event.listens_for(UploadedFile, 'before_delete')
def after_delete_shop_category(mapper, connect, target):
    """Remove file before deletion from BDD"""
    if os.path.exists(target.path()):
        os.remove(target.path())


class NewsletterRecipient(BaseModel):
    """Recipient of the newsletter"""

    name = db.Column(db.VARCHAR(length=150), nullable=False)
    email = db.Column(db.Text(), nullable=False)
    hash = db.Column(db.VARCHAR(length=150), nullable=False)
    confirmed = db.Column(db.Boolean, default=False, nullable=False)

    @classmethod
    def create(cls, name, email, confirmed=False):
        o = cls()
        o.name = name
        o.email = email
        o.hash = secrets.token_urlsafe(nbytes=16)
        o.confirmed = confirmed

        return o

    def get_scrambled_email(self):
        n = len(self.name) % 3
        s = self.email.split('@')
        return s[0][:1 + n] + '***' + (s[0][n - 3:] if len(s[0]) >= 4 else '') + '@***.' + s[1].split('.')[-1]


class Newsletter(BaseModel):
    """Newsletter
    """

    title = db.Column(db.VARCHAR(length=150), nullable=False)
    slug = db.Column(db.VARCHAR(150), nullable=False)
    content = db.Column(db.Text)
    draft = db.Column(db.Boolean, default=True)
    date_published = db.Column(db.DateTime)

    @classmethod
    def create(cls, title, content, draft=True):
        o = cls()
        o.draft = draft
        o.title = title
        o.content = content

        if not draft:
            o.slug = slugify.slugify(title)
            o.date_published = datetime.datetime.now()

        return o


@event.listens_for(Newsletter.title, 'set', named=True)
def receive_newsletter_title_set(target, value, oldvalue, initiator):
    """Set the slug accordingly, but only if it is a draft"""
    if target.draft:
        target.slug = slugify.slugify(value)


class Email(BaseModel):
    title = db.Column(db.VARCHAR(length=150), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    sent = db.Column(db.Boolean(), default=False, nullable=False)

    recipient_id = db.Column(db.Integer, db.ForeignKey('newsletter_recipient.id'))
    recipient = db.relationship('NewsletterRecipient')

    @classmethod
    def create(cls, title, content, recipient_id):
        o = cls()
        o.title = title
        o.content = content
        o.recipient_id = recipient_id

        return o


class MenuEntry(OrderableMixin, BaseModel):

    text = db.Column(db.Text(), nullable=False)
    url = db.Column(db.Text(), nullable=False)
    highlight = db.Column(db.Boolean, default=False, nullable=False)

    @classmethod
    def create(cls, text, url, highlight=False):
        o = cls()
        o.text = text
        o.url = url
        o.highlight = highlight

        # set order
        last_m = MenuEntry.ordered_items(desc=True).first()
        o.order = last_m.order + 1 if last_m else 0

        return o

    def up(self):
        super().up()

    def down(self):
        super().down()
