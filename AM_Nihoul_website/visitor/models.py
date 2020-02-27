import slugify
from sqlalchemy import event

from AM_Nihoul_website import db
from AM_Nihoul_website.base_model import BaseModel


class Page(BaseModel):
    """Page
    """

    title = db.Column(db.VARCHAR(length=150), nullable=False)
    slug = db.Column(db.VARCHAR(150), nullable=False)
    content = db.Column(db.Text)
    protected = db.Column(db.Boolean, default=False, nullable=False)

    @classmethod
    def create(cls, title, text, protected=False):
        o = cls()
        o.title = title
        o.text = text
        o.protected = protected

        return o


@event.listens_for(Page.title, 'set', named=True)
def receive_page_title_set(target, value, oldvalue, initiator):
    """Set the slug accordingly"""
    target.slug = slugify.slugify(value)
