from AM_Nihoul_website import db
from AM_Nihoul_website.base_model import BaseModel


class Page(BaseModel):

    title = db.Column(db.VARCHAR(length=150))
    content = db.Column(db.Text)
