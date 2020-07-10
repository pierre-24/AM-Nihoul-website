from AM_Nihoul_website.tests import TestFlask


class TestPage(TestFlask):

    def test_login(self):
        self.assertTrue(self.login('admin', 'admin'))
        self.assertTrue(self.logout())
