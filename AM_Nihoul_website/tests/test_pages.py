from AM_Nihoul_website.tests import TestFlask


class TestPage(TestFlask):

    def test_login(self):
        self.login()
        self.logout()
