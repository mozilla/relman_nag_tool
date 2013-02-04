import flask, flask.views
import secrets
import os
import functools
import phonebook
import Test
import email_nag
import logging, logging.handlers
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
from simplekv.memory import DictStore
from flaskext.kvsession import KVSessionExtension

# This is to get the routing on the server to recognize it's under a subdomain
class WebFactionMiddleware(object):
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        # TODO - get this from config for local or production dev
        environ['SCRIPT_NAME'] = '/relman_nag'
        return self.app(environ, start_response)

app = flask.Flask(__name__)

# Declaring production globals
DATABASE = '/tmp/flaskr.db'
LOGFILE = '/home/lsblakk/webapps/relman_nag/htdocs/relman_nag.log'

# Check for local_config to override globals
try:
    from local_config import *
except ImportError:
    # no local config found, set the middleware
    app.wsgi_app = WebFactionMiddleware(app.wsgi_app)
    pass

# a DictStore will store everything in memory
# other stores are more useful, like the FilesystemStore, see the simplekv
# documentation for details
store = DictStore()
# this will replace the app's session handling
KVSessionExtension(store, app)

# configuration
app.secret_key = "iphone"
app.config['DEBUG'] = True
app.config.from_object(__name__)

#### LOGGING
format = logging.Formatter(fmt="%(asctime)s-%(levelname)s-%(funcName)s: %(message)s")
handler = logging.handlers.RotatingFileHandler(LOGFILE, maxBytes=50000, backupCount=5)
handler.setFormatter(format)
app.logger.addHandler(handler)

#db = SQLAlchemy(app)
def connect_db():
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

def get_templates():
    cur = g.db.execute('select id,template_title from list_templates order by id desc')
    list_templates = [dict(template_id=row[0],template_title=row[1]) for row in cur.fetchall()]
    print list_templates
    return list_templates

def get_selected_template(template_id):
    cur = g.db.execute('select id,template_title,template_body from list_templates where id='+template_id)
    selected_template = [dict(template_id=row[0],template_title=row[1],template_body=row[2]) for row in cur.fetchall()]
    print selected_template
    return selected_template

def get_selected_query(query_id):
    cur = g.db.execute('select query_name,query_channel,query_url from queries where id='+query_id)
    selected_query = [dict(query_name=row[0],query_channel=row[1],query_url=row[2]) for row in cur.fetchall()]
    print selected_query
    return selected_query

def get_selected_queries(query_id_list):
	selected_query=[]
	for query_id in query_id_list :
		cur = g.db.execute('select query_name,query_channel,query_url from queries where id='+query_id)
		for row in cur.fetchall():
			selected_query.append(dict(query_name=row[0],query_channel=row[1],query_url=row[2]))
	print selected_query
	return selected_query

def delete_template(template_id):
    cur = g.db.execute('Delete from list_templates where id='+template_id)
    g.db.commit()
    #selected_template = [dict(template_title=row[0],template_body=row[1]) for row in cur.fetchall()]
    print cur
    #return selected_template

def delete_query(query_id):
    cur = g.db.execute('Delete from queries where id='+query_id)
    g.db.commit()
    print cur
    

def get_queries():
    cur_query = g.db.execute('select id,query_name from queries order by id desc')
    queries = [dict(query_id=row[0],query_name=row[1]) for row in cur_query.fetchall()]
    print queries
    return queries


class Main(flask.views.MethodView):
    def get(self):
        try:
            flask.session['people'] = phonebook.PhonebookDirectory(secrets.USERNAME,secrets.PASSWD);
        except Exception:
            app.logger.debug("DEBUG: Exception in getting phonebook: %s" % Exception.message)
            flask.flash("Could not pull the phonebook")
            return flask.redirect(flask.url_for('index'))
        return flask.redirect(flask.url_for('show_templates'))

class Show_Templates(flask.views.MethodView):
    def get(self):
        return flask.render_template('show_templates.html',list_templates  = get_templates())

	def post(self):
		if 'create_template' in flask.request.form:
			return flask.redirect(flask.url_for('create_template'))
					      #return flask.redirect(flask.url_for('show_templates'))
		if 'buttonclicked' in flask.request.form:
			template_id_list = flask.request.form.getlist('template_id')
			print template_id_list
			print "*****",flask.request.form['buttonclicked']
			if flask.request.form['buttonclicked'] == 'use_template' :
				numids = len(template_id_list)
				if  numids != 1:
					flask.flash("Please select exactly one template")
					return flask.redirect(flask.url_for(show_templates))
				else :
					return flask.redirect(flask.url_for('use_template',id=template_id_list[0]))
			
			elif flask.request.form['buttonclicked'] == 'edit_template' :
				numids = len(template_id_list)
				if  numids != 1:
					flask.flash("Please select exactly one template")
					return flask.redirect(flask.url_for(show_templates))
				else :
					return flask.redirect(flask.url_for('edit_template',id=template_id_list[0]))
			else :
				return flask.redirect(flask.url_for('delete_template',idlist=template_id_list))
					      

class Use_Template(flask.views.MethodView):
	
	def get(self):
		template_id = request.args.get('id')
		print template_id
		return flask.render_template('use_template.html',selected_template = get_selected_template(template_id))
	
	
	def post(self):
		#flask.flash("Not implemented")
		if 'Next' in flask.request.form:
			print "***Next\n"
			print "***Next1\n"
			#return flask.redirect(flask.url_for('use_template'))
			print "***Next\n"
			flask.session['modified_template'] = flask.request.form['template_body']
			print flask.session['modified_template']
			return flask.redirect(flask.url_for('show_queries'))
					      #return flask.redirect(flask.url_for('show_templates'))

class Use_Query(flask.views.MethodView):
	
	def get(self):
		
		query_id_list = request.args.getlist('idlist')
		#print query_id_list+"list"
		print "***Useget******\n"
		print flask.session['modified_template']
		flask.session['queries'] = get_selected_queries(query_id_list)
		print "\nprinting from session\n"
		print flask.session['queries']
		try :
			email_nag.nagEmailScript()
			last_msg, msg = email_nag.getMessage("",False)
			print "******BB*********\n\n\n",msg
			if last_msg:
				return flask.render_template('show_last_message.html',last_msg = msg  )
			else:
				return flask.redirect(flask.url_for('show_message',show_msg=msg))
		except Exception, e :
			print "\nException:\n"
			print Exception,e
	
	
	def post(self):
		#flask.flash("Not implemented")
		#if 'use_query' in flask.request.form:
			print "***Use\n"
			#return flask.redirect(flask.url_for('use_template'))
			print modified_template
			return flask.redirect(flask.url_for('show_queries'))
					      #return flask.redirect(flask.url_for('show_templates'))

class Delete_Template(flask.views.MethodView):
	
	def get(self):
		template_id_list = request.args.getlist('idlist')
		print template_id_list
		for template_id in template_id_list:
			delete_template(template_id)
		return flask.redirect(flask.url_for('show_templates'))
	
	
	def post(self):
		#flask.flash("Not implemented")
		if 'use_template' in flask.request.form:
			return flask.redirect(flask.url_for('delete_template'))
					      #return flask.redirect(flask.url_for('show_templates'))

class Delete_Query(flask.views.MethodView):
	
	def get(self):
		query_id_list = request.args.getlist('idlist')
		print query_id_list
		for query_id in query_id_list:
			delete_query(query_id)
		return flask.redirect(flask.url_for('show_queries'))
	
	
	def post(self):
		#flask.flash("Not implemented")
		if 'use_query' in flask.request.form:
			return flask.redirect(flask.url_for('delete_query'))
					      #return flask.redirect(flask.url_for('show_templates'))

class Create_Template(flask.views.MethodView):
	
	def get(self):
		print "\n in ****** create template"
		return flask.render_template('create_template.html')
	
	
	def post(self):
		print "\n in ****** create template"
		g.db.execute('insert into list_templates (template_title, template_body) values (?, ?)',[request.form['template_title'], request.form['template_body']])
		g.db.commit()
		flask.flash('New entry was successfully posted')
		return flask.redirect(flask.url_for('show_templates'))

class Create_Query(flask.views.MethodView):
	
	def get(self):
		print "\n in ****** create query"
		return flask.render_template('create_query.html')
	
	
	def post(self):
		print "\n in ****** create query"
		g.db.execute('insert into queries (query_name, query_channel, query_url) values (?, ?, ?)',[request.form['query_name'], request.form['query_channel'], request.form['query_url']])
		g.db.commit()
		flask.flash('New entry was successfully posted')
		return flask.redirect(flask.url_for('show_queries'))

class Show_Queries(flask.views.MethodView):
	
	def get(self):
		return flask.render_template('show_queries.html',queries  = get_queries())
	
	
	def post(self):
		if 'create_query' in flask.request.form:
			return flask.redirect(flask.url_for('create_query'))
		if 'querybuttonclicked' in flask.request.form:
			query_id_list = flask.request.form.getlist('query_id')
			print query_id_list
			print "*****",flask.request.form['querybuttonclicked']
			if flask.request.form['querybuttonclicked'] == 'use_query' :
				
				return flask.redirect(flask.url_for('use_query',idlist=query_id_list))
			else :
				return flask.redirect(flask.url_for('delete_query',idlist=query_id_list))
		#flask.flash("Not implemented")
		#def post(self):
		#flask.flash("Not implemented")
		#if 'use_template' in flask.request.form:
			#return flask.redirect(flask.url_for('show_queries'))

class Edit_Template(flask.views.MethodView):
	
	def get(self):
		template_id = request.args.get('id')
		print template_id
		return flask.render_template('edit_template.html',selected_template = get_selected_template(template_id))
	
	
	
	def post(self):
		if 'Save' in flask.request.form:
			template_id = request.form['template_id']
			modified_template_body = request.form['template_body']
			print "\najjsj\n"
			Test.test_session_variable()
			print modified_template_body
			print template_id
			
			g.db.execute('update list_templates SET template_body=\"'+modified_template_body+'\" where id='+template_id)
			g.db.commit()
			flask.flash('New entry was successfully saved')
			return flask.redirect(flask.url_for('show_templates'))

class Show_Message(flask.views.MethodView):
	
	def get(self):
		msg = request.args.get('show_msg')
		return flask.render_template('show_message.html',msg = msg)
	
	
	def post(self):
		send = False
		if 'Send' in flask.request.form:
			send = True
		msgToSend = request.form['msg_body']
		try :
			last_msg, msg = email_nag.getMessage(msgToSend,send)
			print "******BB*********\n\n\n",msg
			if last_msg:
				return flask.render_template('show_last_message.html',last_msg = msg  )
			else:
				return flask.render_template('show_message.html',msg = msg)
		except Exception :
			print "\nException:"
			print Exception

 

app.add_url_rule('/',view_func=Main.as_view('index'), methods=['GET'])
app.add_url_rule('/show_templates', view_func=Show_Templates.as_view('show_templates'), methods=['GET','POST'])
app.add_url_rule('/create_template', view_func=Create_Template.as_view('create_template'), methods=['GET','POST'])
app.add_url_rule('/use_template', view_func=Use_Template.as_view('use_template'), methods=['GET','POST'])
app.add_url_rule('/use_query', view_func=Use_Query.as_view('use_query'), methods=['GET','POST'])
app.add_url_rule('/delete_template', view_func=Delete_Template.as_view('delete_template'), methods=['GET','POST'])
app.add_url_rule('/delete_query', view_func=Delete_Query.as_view('delete_query'), methods=['GET','POST'])
app.add_url_rule('/show_queries', view_func=Show_Queries.as_view('show_queries'), methods=['GET','POST'])
app.add_url_rule('/create_query', view_func=Create_Query.as_view('create_query'), methods=['GET','POST'])
app.add_url_rule('/edit_template', view_func=Edit_Template.as_view('edit_template'), methods=['GET','POST'])
app.add_url_rule('/show_message', view_func=Show_Message.as_view('show_message'), methods=['GET','POST'])

if __name__ == '__main__':
    app.debug = True
    app.run()
