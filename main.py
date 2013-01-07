# -*- coding: utf-8 -*-
"""
c-base einkauf-o-matic
"""

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
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

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


@app.route('/addqueue', methods=['POST'])
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


if __name__ == "__main__":
    app.run()