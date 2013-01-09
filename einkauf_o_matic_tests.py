#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
c-base einkauf-o-matic - unittests
"""

import os
import einkauf_o_matic
import unittest
import tempfile


class EinkaufOMaticTestCase(unittest.TestCase):
    """
    unittests for the einkauf-o-matic
    """

    def setUp(self):
        """
        just setting things up
        """
        self.db_fd, einkauf_o_matic.app.config['DATABASE'] = tempfile.mkstemp()
        einkauf_o_matic.app.config['TESTING'] = True
        self.app = einkauf_o_matic.app.test_client()
        einkauf_o_matic.init_db()

    def tearDown(self):
        """
        delete the temporary db after all tests are done
        """
        os.close(self.db_fd)
        os.unlink(einkauf_o_matic.app.config['DATABASE'])

    # helper functions

    def login(self, username, password):
        """
        logs the given user in
        """
        return self.app.post('/login', data=dict(
            username=username,
            password=password
            ), follow_redirects=True)

    def logout(self):
        """
        logs the user off
        """
        return self.app.get('/logout', follow_redirects=True)

    def register(self, member, password, password2=None):
        """
        Helper function to register a user
        """
        if password2 is None:
            password2 = password
        return self.app.post('/register', data={
            'member':       member,
            'password':     password,
            'password2':    password2
        }, follow_redirects=True)

    # testing functions

    def test_root_page(self):
        """
        test if the app shows "You must be logged in to see something useful
        here" if we access root (/)
        """
        rv = self.app.get('/')
        assert 'You must be logged in to see something useful here' in rv.data

    def test_register(self):
        """
        Make sure registering works
        """
        rv = self.register('horst', 'passw0rd')
        assert 'You were successfully registered ' \
               'and can login now' in rv.data
        rv = self.register('horst', 'passw0rd')
        assert 'The username is already taken' in rv.data
        rv = self.register('', 'passw0rd')
        assert 'You have to enter a username' in rv.data
        rv = self.register('harry', '')
        assert 'You have to enter a password' in rv.data
        rv = self.register('harry', 'passw0rd', 'p@ssword')
        assert 'The two passwords do not match' in rv.data

    def test_login_logout(self):
        rv = self.login('root', 'toor')
        assert 'You were logged in' in rv.data
        rv = self.logout()
        assert 'You were logged out' in rv.data
        rv = self.login('wronguser', 'toor')
        assert 'Invalid username' in rv.data
        rv = self.login('root', 'wrongpass')
        assert 'Invalid password' in rv.data

    def test_add_store(self):
        self.login('root', 'toor')
        rv = self.app.post('/addstore', data=dict(
            name='adafruit INDUSTRIES',
            url='http://adafruit.com/',
            minorder='250'
        ), follow_redirects=True)
        assert 'No stores here so far' not in rv.data
        assert '<a href="http://adafruit.com/">adafruit INDUSTRIES' in rv.data

    def test_add_queue(self):
        self.login('root', 'toor')
        rv = self.app.post('/add', data=dict(
            title='raspberrypi stuff',
            deadline='2012-01-30',
            store='0'
        ), follow_redirects=True)
        assert 'No stores here so far' not in rv.data
        assert 'raspberrypi stuff' in rv.data and '2012-01-30' in rv.data


if __name__ == '__main__':
    unittest.main()