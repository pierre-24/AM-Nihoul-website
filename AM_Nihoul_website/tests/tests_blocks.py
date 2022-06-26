import flask
from bs4 import BeautifulSoup

from AM_Nihoul_website import db
from AM_Nihoul_website.visitor.models import Block
from AM_Nihoul_website.tests import TestFlask


class TestsBlock(TestFlask):

    def setUp(self):
        super().setUp()

        # NOTE: for the order to be set, each one should be added individually
        self.block_1 = Block.create('test1', 'col-lg-4 col-md-6')
        db.session.add(self.block_1)
        db.session.commit()

        self.block_2 = Block.create('test2', 'col-lg-4 col-md-6')
        db.session.add(self.block_2)
        db.session.commit()

        self.block_3 = Block.create('test1', 'col-lg-4 col-md-12')
        db.session.add(self.block_3)
        db.session.commit()

        self.num_blocks = Block.query.count()
        self.login()

    def test_block_create_ok(self):
        self.assertEqual(Block.query.count(), self.num_blocks)

        text = 'other test'
        attributes = 'col-12'

        response = self.client.post(flask.url_for('admin.block-create'), data={
            'content': text,
            'attributes': attributes,
            'is_create': 1,
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Block.query.count(), self.num_blocks + 1)

        c = Block.query.order_by(Block.id.desc()).first()
        self.assertIsNotNone(c)
        self.assertEqual(c.text, text)
        self.assertEqual(c.attributes, attributes)

    def test_block_create_not_admin_ko(self):
        self.assertEqual(Block.query.count(), self.num_blocks)
        self.logout()

        text = 'other test'
        attributes = 'col-12'

        response = self.client.post(flask.url_for('admin.block-create'), data={
            'content': text,
            'attributes': attributes,
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Block.query.count(), self.num_blocks)

    def test_block_edit_ok(self):
        text = 'xyz'
        attributes = 'col-12'

        response = self.client.post(flask.url_for('admin.block-edit', id=self.block_3.id), data={
            'content': text,
            'attributes': attributes,
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        c = Block.query.get(self.block_3.id)
        self.assertEqual(c.text, text)
        self.assertEqual(c.attributes, attributes)

    def test_block_edit_not_admin_ko(self):
        text = 'xyz'
        attributes = 'http://x.com/b2.html'
        self.logout()

        response = self.client.post(flask.url_for('admin.block-edit', id=self.block_3.id), data={
            'content': text,
            'attributes': attributes
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        c = Block.query.get(self.block_3.id)
        self.assertNotEqual(c.text, text)
        self.assertNotEqual(c.attributes, attributes)

    def test_block_delete_ok(self):
        self.assertEqual(Block.query.count(), self.num_blocks)

        response = self.client.delete(flask.url_for('admin.block-delete', id=self.block_3.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Block.query.count(), self.num_blocks - 1)
        self.assertIsNone(Block.query.get(self.block_3.id))

    def test_block_delete_not_admin_ko(self):
        self.assertEqual(Block.query.count(), self.num_blocks)
        self.logout()

        response = self.client.delete(flask.url_for('admin.block-delete', id=self.block_3.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Block.query.count(), self.num_blocks)
        self.assertIsNotNone(Block.query.get(self.block_3.id))

    def test_block_move_ok(self):
        self.assertEqual(
            Block.ordered_items().all(), [self.block_1, self.block_2, self.block_3])

        self.client.get(flask.url_for('admin.block-move', id=self.block_1.id, action='up'))
        self.assertEqual(
            Block.ordered_items().all(), [self.block_2, self.block_1, self.block_3])

        self.client.get(flask.url_for('admin.block-move', id=self.block_1.id, action='down'))
        self.assertEqual(
            Block.ordered_items().all(), [self.block_1, self.block_2, self.block_3])

    def test_block_move_not_admin_ko(self):
        self.assertEqual(
            Block.ordered_items().all(), [self.block_1, self.block_2, self.block_3])
        self.logout()

        r = self.client.get(flask.url_for('admin.block-move', id=self.block_1.id, action='up'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            Block.ordered_items().all(), [self.block_1, self.block_2, self.block_3])

        self.client.get(flask.url_for('admin.block-move', id=self.block_2.id, action='down'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            Block.ordered_items().all(), [self.block_1, self.block_2, self.block_3])

    def test_blocks_on_homepage_ok(self):
        self.logout()

        response = self.client.get(flask.url_for('visitor.index'))
        self.assertEqual(response.status_code, 200)

        bs = BeautifulSoup(response.text, 'html.parser')
        blocks = bs.find_all(class_='block')

        self.assertEqual(
            [b.parent['class'] for b in blocks],
            [b.attributes.split() for b in [self.block_1, self.block_2, self.block_3]]
        )

        self.assertEqual(
            [b.text.strip() for b in blocks],
            [b.text for b in [self.block_1, self.block_2, self.block_3]]
        )
