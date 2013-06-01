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
from flask import send_from_directory
from contextlib import closing
import os

from item_crawler import ItemCrawler


# configuration
DATABASE = 'einkaufomatic.db'
SECRET_KEY = 'development key'
DEBUG = True
USERNAME = 'root'
PASSWORD = 'toor'
MEMBERID = 1337

# create the application
APP = Flask(__name__)
APP.config.from_object(__name__)
APP.config.from_envvar('EINKAUFOMATIC_SETTINGS', silent=True)


# initialize stuff
def connect_db():
    """
    let the application connect to the given database
    """
    return sqlite3.connect(APP.config['DATABASE'])


def init_db():
    """
    create database
    """
    with closing(connect_db()) as database:
        with APP.open_resource('schema.sql') as sqlfile:
            database.cursor().executescript(sqlfile.read())
        database.commit()


@APP.before_request
def before_request():
    """
    connect to the database before doing something
    """
    g.db = connect_db()


@APP.teardown_request
def teardown_request(exception):
    """
    disconnect database after execution
    """
    if exception is not None:
        print exception
    g.db.close()

# routes


@APP.route('/favicon.ico')
def favicon():
    """
    return the favicon
    """
    return send_from_directory(os.path.join(APP.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@APP.route('/')
def show_queues():
    """
    root dir shows active queues
    """
    cur = g.db.execute('select id, owner, (select name from stores where \
                        id=store) as store, title, deadline, status from \
                        queues order by deadline asc')
    queues = [dict(id=row[0], owner=row[1], store=row[2], title=row[3],
                   deadline=row[4], status=row[5])
              for row in cur.fetchall()]
    return render_template('show_queues.html', queues=queues)


@APP.route('/<int:queue_id>', methods=['GET'])
def show_queue(queue_id):
    """
    show the queue with the given id
    """
    cur = g.db.execute('select id, member, name, num, price, url, paid from \
                        items where queue=' + str(queue_id) +
                        ' order by member asc, name asc')
    items = [dict(id=row[0], member=row[1], name=row[2], num=row[3],
                  price=row[4], url=row[5], paid=row[6])
             for row in cur.fetchall()]
    cur = g.db.execute('select id, urls, minorder, currency, shipping from \
                        stores where id=(select store from queues where id=' +
                        str(queue_id) + ')')
    stores = [dict(id=row[0], urls=row[1], minorder=row[2], currency=row[3],
                   shipping=row[4])
             for row in cur.fetchall()]

    totalprice = stores[0].get('shipping')
    totalpaid = 0
    totalitems = 0
    for item in items:
        totalprice += item.get('num') * item.get('price')
        totalpaid += item.get('paid')
        totalitems += item.get('num')
    return render_template('show_queue.html', items=items, queue_id=queue_id,
                           store=stores[0], totalprice=totalprice,
                           totalpaid=totalpaid, totalitems=totalitems)


@APP.route('/<int:queue_id>', methods=['POST'])
def add_item(queue_id):
    """
    add the given item to the open queue and show the updated queue
    """
    if not session.get('logged_in'):
        abort(401)

    crawler = ItemCrawler()
    item = crawler.get_item(request.form['url'], request.form['num'])
    if not item == 'timeout':
        cur = g.db.execute('select id, num from items where queue=? and \
                            member=? and url=?', [queue_id,
                            session.get('member'), request.form['url']])
        items = [dict(id=row[0], num=row[1])
                 for row in cur.fetchall()]
        if len(items) > 0:
            g.db.execute('update items set num=? where id=?',
                         [items[0]['num'] + int(request.form['num']),
                          items[0]['id']])
            g.db.commit()
        else:
            g.db.execute('insert into items (queue, member, name, num, price, \
                          url, img_url, paid) values (?, ?, ?, ?, ?, ?, ?, ?)',
                         [queue_id, session.get('member'), item['name'],
                          request.form['num'], item['price'],
                          request.form['url'], item['image_url'], 0])
            g.db.commit()
        flash('New item was successfully added to queue')
    else:
        flash('The site could not be reached within a given time. \
               No item added.')
    return redirect(url_for('show_queue', queue_id=queue_id))


@APP.route('/<int:queue_id>/edit', methods=['GET'])
def show_edit_queue(queue_id):
    """
    show the queue with the given id for edit
    """
    cur = g.db.execute('select id, title, store, deadline, status from queues \
                        where id=' + str(queue_id))
    queues = [dict(id=row[0], title=row[1], store=row[2], deadline=row[3],
                   status=row[4])
              for row in cur.fetchall()]
    if not queues.count > 0:
        flash('No editable queue was found (id: ' + str(queue_id) + ').')
        return redirect(url_for('show_queues'))
    else:
        cur = g.db.execute('select id, name, minorder from stores \
                            order by name asc')
        stores = [dict(id=row[0], name=row[1], minorder=row[2])
                  for row in cur.fetchall()]
        return render_template('edit_queue.html', queue=queues[0],
                               stores=stores, queue_id=queue_id)


@APP.route('/<int:queue_id>/edit', methods=['POST'])
def edit_queue(queue_id):
    """
    show the queue with the given id for edit
    """
    if not session.get('logged_in'):
        abort(401)
    cur = g.db.execute('select id from queues where id=' + str(queue_id))
    queues = [dict(id=row[0])
              for row in cur.fetchall()]
    if not len(queues) == 1:
        flash('No updatable queue was found (id: ' + str(queue_id) + ').')
        return redirect(url_for('show_queues'))
    else:
        g.db.execute('update queues set store=?, title=?, deadline=?, \
                      status=? where id=' + str(queue_id),
                      request.form['store'], request.form['title'],
                      request.form['deadline'], request.form['status'])
        g.db.commit()
        flash('New queue was successfully posted')
        return redirect(url_for('show_queue', queue_id=queue_id))


@APP.route('/add', methods=['GET'])
def show_add_queue():
    """
    show form to add new queues
    """
    cur = g.db.execute('select id, name, minorder from stores order by name \
                        asc')
    stores = [dict(id=row[0], name=row[1], minorder=row[2])
              for row in cur.fetchall()]
    return render_template('add_queue.html', stores=stores)


@APP.route('/add', methods=['POST'])
def add_queue():
    """
    add new queue to the database
    """
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into queues (owner, store, title, deadline, status) \
                  values (?, ?, ?, ?, ?)',
                 [session.get('member'),
                  request.form['store'],
                  request.form['title'],
                  request.form['deadline'],
                  'in progress'])
    g.db.commit()
    flash('New queue was successfully posted')
    return redirect(url_for('show_queues'))


@APP.route('/stores')
def show_stores():
    """
    show the active stores
    """
    cur = g.db.execute('select id, name, urls, minorder, state, currency, \
                        shipping, comment from stores order by name asc')
    stores = [dict(id=row[0], name=row[1], urls=row[2], minorder=row[3],
                   state=row[4], currency=row[5], shipping=row[6],
                   comment=row[7])
              for row in cur.fetchall()]
    return render_template('show_stores.html', stores=stores)


@APP.route('/store/add', methods=['GET'])
def show_add_store():
    """
    show the form to submit a new store
    """
    return render_template('add_store.html')


@APP.route('/store/add', methods=['POST'])
def add_store():
    """
    add a new store to the database
    """
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into stores (name, urls, minorder, state, currency, \
                  shipping, comment) values (?, ?, ?, ?, ?, ?, ?)',
                 [request.form['name'], request.form['urls'],
                  request.form['minorder'], request.form['state'],
                  request.form['currency'], request.form['shipping'],
                  request.form['comment']])
    g.db.commit()
    flash('New store was successfully posted')
    return redirect(url_for('show_stores'))


@APP.route('/additem/<url>', methods=['GET'])
def auto_add_item(url):
    """
    function used by the bookmarklet to add new items
    """
    # check if the store is supportet
        # not check if there is a queue with this store currently running
            # create a new queue with this store
        # some cool logic to find the item and add the needed values
    return render_template('add_item')

# internal functions


@APP.route('/login', methods=['GET', 'POST'])
def login():
    """
    logs the user in or displays a login form
    """
    error = None
    if request.method == 'POST':
        if request.form['username'] != APP.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != APP.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            session['member'] = MEMBERID
            flash('You were logged in')
            return redirect(url_for('show_queues'))
    return render_template('login.html', error=error)


@APP.route('/logout')
def logout():
    """
    logs the user out
    """
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_queues'))


if __name__ == "__main__":
    APP.run(debug=DEBUG)
