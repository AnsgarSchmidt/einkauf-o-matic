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


# configuration
DATABASE = 'einkaufomatic.db'
SECRET_KEY = 'development key'
DEBUG = True
USERNAME = 'root'
PASSWORD = 'toor'
MEMBERID = 1337

# create the application
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('EINKAUFOMATIC_SETTINGS', silent=True)

# initialize stuff


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
    cur = g.db.execute('select id, owner, (select name from stores where id=store) as store, title, deadline, status from queues order by deadline asc')
    queues = [dict(id=row[0], owner=row[1], store=row[2], title=row[3], deadline=row[4], status=row[5])
              for row in cur.fetchall()]
    return render_template('show_queues.html', queues=queues)


@app.route('/<int:queue_id>', methods=['GET'])
def show_queue(queue_id):
    """
    show the queue with the given id
    """
    cur = g.db.execute('select id, member, name, num, price, url, paid from items where queue=' + str(queue_id) + ' order by member asc')
    items = [dict(id=row[0], member=row[1], name=row[2], num=row[3], price=row[4], url=row[5], paid=row[6])
             for row in cur.fetchall()]
    cur = g.db.execute('select id, url, minorder, currency, shipping from stores where id=(select store from queues where id=' + str(queue_id) + ')')
    stores = [dict(id=row[0], url=row[1], minorder=row[2], currency=row[3], shipping=row[4])
             for row in cur.fetchall()]

    totalprice = 0
    totalpaid = 0
    for item in items:
        totalprice += item.get('num')*item.get('price')
        totalpaid += item.get('paid')
    return render_template('show_queue.html', items=items, queue_id=queue_id, store=stores[0], totalprice=totalprice, totalpaid=totalpaid)


@app.route('/<int:queue_id>', methods=['POST'])
def add_item(queue_id):
    """
    add the given item to the open queue and show the updated queue
    """
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into items (queue, member, name, num, price, url, paid) values (?, ?, ?, ?, ?, ?, ?)',
                 [queue_id,
                  session.get('member'),
                  request.form['name'],
                  request.form['num'],
                  request.form['price'],
                  request.form['url'],
                  0])
    g.db.commit()
    flash('New item was successfully added to queue')
    return redirect(url_for('show_queue', queue_id=queue_id))


#TODO
@app.route('/<int:queue_id>/edit', methods=['GET'])
def edit_queue(queue_id):
    """
    show the queue with the given id for edit
    """
    cur = g.db.execute('select member, (select nick from members where id=member) as nick, name, num, price, url, paid from items where queue=' + str(queue_id))
    queue = [dict(member=row[0], nick=row[1], name=row[2], num=row[3], price=row[4], url=row[5], paid=row[6])
             for row in cur.fetchall()]
    return render_template('edit_queue.html', queue=queue, queue_id=queue_id)


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
    g.db.execute('insert into queues (owner, store, title, deadline, status) values (?, ?, ?, ?, ?)',
                 [session.get('member'),
                  request.form['store'],
                  request.form['title'],
                  request.form['deadline'],
                  'in progress'])
    g.db.commit()
    flash('New queue was successfully posted')
    return redirect(url_for('show_queues'))


@app.route('/stores')
def show_stores():
    cur = g.db.execute('select id, name, url, minorder, state, currency, shipping, comment from stores order by name asc')
    stores = [dict(id=row[0], name=row[1], url=row[2], minorder=row[3], state=row[4], currency=row[5], shipping=row[6], comment=row[7])
              for row in cur.fetchall()]
    return render_template('show_stores.html', stores=stores)


@app.route('/store/add', methods=['GET'])
def show_add_store():
    return render_template('add_store.html')


@app.route('/store/add', methods=['POST'])
def add_store():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into stores (name, url, minorder, state, currency, shipping, comment) values (?, ?, ?, ?, ?, ?, ?)',
                 [request.form['name'],
                  request.form['url'],
                  request.form['minorder'],
                  request.form['state'],
                  request.form['currency'],
                  request.form['shipping'],
                  request.form['comment']])
    g.db.commit()
    flash('New store was successfully posted')
    return redirect(url_for('show_stores'))

# internal functions


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
            session['member'] = MEMBERID
            flash('You were logged in')
            return redirect(url_for('show_queues'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_queues'))


if __name__ == "__main__":
    app.run(debug=DEBUG)