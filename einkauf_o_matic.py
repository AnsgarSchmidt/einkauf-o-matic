#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
c-base einkauf-o-matic

@author: Ricardo (XenGi) Band <me@xengi.de>

    This file is part of einkauf-o-matic.

    einkauf-o-matic is licensed under Attribution-NonCommercial-ShareAlike 3.0
    Unported (CC BY-NC-SA 3.0).

    <http://creativecommons.org/licenses/by-nc-sa/3.0/>
"""

__author__ = "Ricardo (XeN) Band <xen@c-base.org>"
__copyright__ = "Copyright (C) 2012 Ricardo Band"
__revision__ = "$Id$"
__version__ = "0.1"


import sqlite3
from flask import Flask
from flask import request
from flask import session
from flask import g
from flask import redirect
from flask import url_for
from flask import abort
from flask import render_template
from flask import flash
from contextlib import closing
from random import random
from string import ascii_letters, digits
from hashlib import sha1


# configuration
DATABASE = 'einkaufomatic.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'root'
PASSWORD = 'toor'

# create the application
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('EINKAUFOMATIC_SETTINGS', silent=True)


def connect_db():
    """
    let the application connect to the given database
    """
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    g.db.close()


# routes
@app.route('/')
def show_queues():
    cur = g.db.execute('select * from queues order by deadline desc')
    queues = [dict(id=row[0], store=row[1], title=row[2], deadline=row[3])
              for row in cur.fetchall()]
    cur = g.db.execute('select * from stores order by name asc')
    stores = [dict(id=row[0], name=row[1])
              for row in cur.fetchall()]
    return render_template('show_queues.html', queues=queues, stores=stores)


@app.route('/queues/<int:queue_id>', methods=['GET'])
def show_queue(queue_id):
    """
    show the queue with the given id
    """
    cur = g.db.execute('select member, (select nick from members where id=member) as nick, name, num, price, url, paid from items where queue=' + str(queue_id))
    queue = [dict(member=row[0], nick=row[1], name=row[2], num=row[3], price=row[4], url=row[5], paid=row[6])
             for row in cur.fetchall()]
    return render_template('show_queue.html', queue=queue, queue_id=queue_id)


@app.route('/queues/<int:queue_id>', methods=['POST'])
def add_item(queue_id):
    """
    add an item to the queue
    """
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into items (queue, name, num, price, member, url, paid) values (?, ?, ?, ?, ?, ?, ?)',
                 [queue_id,
                  request.form['name'],
                  request.form['num'],
                  request.form['price'],
                  member_id,
                  request.form['url'],
                  0])
    g.db.commit()
    flash('New queue was successfully posted')
    return redirect(url_for('show_queues'))


@app.route('/add', methods=['GET'])
def show_add_queue():
    cur = g.db.execute('select id, title, store, deadline from queues order by store asc')
    queues = [dict(id=row[0], title=row[1], store=row[2], deadline=row[3])
              for row in cur.fetchall()]
    cur = g.db.execute('select id, name, minorder from stores order by name asc')
    stores = [dict(id=row[0], name=row[1], minorder=row[2])
              for row in cur.fetchall()]
    return render_template('add_queue.html', queues=queues, stores=stores)


@app.route('/add', methods=['POST'])
def add_queue():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into queues (store, title, deadline) values (?, ?, ?)',
                 [request.form['store'],
                  request.form['title'],
                  request.form['deadline']])
    g.db.commit()
    flash('New queue was successfully posted')
    return redirect(url_for('show_queues'))


@app.route('/stores')
def show_stores():
    cur = g.db.execute('select * from stores order by name asc')
    stores = [dict(id=row[0], name=row[1], url=row[2], minorder=row[3])
              for row in cur.fetchall()]
    return render_template('show_stores.html', stores=stores)


@app.route('/addstore', methods=['GET'])
def show_add_store():
    cur = g.db.execute('select * from stores order by name asc')
    stores = [dict(id=row[0], name=row[1], url=row[2], minorder=row[3])
              for row in cur.fetchall()]
    return render_template('add_store.html', stores=stores)


@app.route('/addstore', methods=['POST'])
def add_store():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into stores (name, url, minorder) values (?, ?, ?)',
                 [request.form['name'],
                  request.form['url'],
                  request.form['minorder']])
    g.db.commit()
    flash('New store was successfully posted')
    return redirect(url_for('show_stores'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_queues'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_queues'))


@app.route('/register', methods=['GET'])
def show_register():
    cur = g.db.execute('select nick from members order by nick asc')
    members = [dict(nick=row[1])
              for row in cur.fetchall()]
    return render_template('register.html', members=members)


@app.route('/register', methods=['POST'])
def register():
    salt = ''.join(random.choice(ascii_letters + digits) for x in range(6))
    g.db.execute('insert into members (nick, hash, salt, status) values (?, ?, ?, ?)',
                 [request.form['nick'],
                  sha1(request.form['pass'] + salt),
                  salt,
                  'inactive'])
    g.db.commit()
    flash('New store was successfully posted')
    return redirect(url_for('show_queues'))


if __name__ == "__main__":
    app.run()