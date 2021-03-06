# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL('sqlite://storage.sqlite')
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db)
crud, service, plugins = Crud(db), Service(), PluginManager()

db.define_table(
	auth.settings.table_user_name,
	Field('first_name', length=128, default=''),
	Field('last_name', length=128, default=''),
	Field('email', length=128, default='', unique=True),
	Field('password', 'password', length=512,
		readable=False, label='Password'),
	Field('registration_key', length=512,
		writable=False, readable=False, default=''),
	Field('reset_password_key', length=512,
		writable=False, readable=False, default=''),
	Field('registration_id', length=512,
		writable=False, readable=False, default=''),
	Field('username', length=40),
	Field('puntos','integer'), #puntos que puede dar
	Field('avatar','upload'),
	)
custom_auth_table = db[auth.settings.table_user_name] # get the custom_auth_table
custom_auth_table.username.requires = IS_NOT_IN_DB(db, custom_auth_table.username)
custom_auth_table.first_name.requires = \
	IS_NOT_EMPTY(error_message=auth.messages.is_empty)
custom_auth_table.last_name.requires = \
	IS_NOT_EMPTY(error_message=auth.messages.is_empty)
custom_auth_table.password.requires = [CRYPT()]
custom_auth_table.email.requires = [
	IS_EMAIL(error_message=auth.messages.invalid_email),
	IS_NOT_IN_DB(db, custom_auth_table.email)]
auth.settings.table_user = custom_auth_table # tell auth to use custom_auth_table

custom_auth_table.puntos.default = 3
custom_auth_table.puntos.writable = False
custom_auth_table.puntos.readable = False

def puntos_totales(user):
		""" Retorna la cantidad de puntos que tiene el usuario especificado """
		user = db.auth_user(user)
		posts = db(db.post.autor==user.id).select()
		puntos = sum([post.puntos for post in posts])
		return puntos
custom_auth_table.puntos_totales = puntos_totales
def rango(user):
		""" Retorna la traducción de Novato o New Full User según el rango
		del usuario """
		if db( (db.post.puntos>=50) & (db.post.autor==user) ).select():
				return T("New Full User")
		else:
				return T("Novato")
custom_auth_table.rango = rango

## create all tables needed by auth if not custom tables
auth.define_tables(username=True, signature=False)
#auth.settings.extra_fields[auth.settings.table_user_name] = \
#		[Field('puntos',default = 10)]

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'you@gmail.com'
mail.settings.login = 'username:password'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth, filename='private/janrain.key')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)

db.define_table('categoria',
		Field('nombre'),
		Field('identifier'),
		)

db.define_table('post',
		Field('autor',db.auth_user, required=True),
		Field('titulo'),
		Field('categoria', db.categoria),
		Field('contenido', 'text'),
		Field('puntos', 'integer'),
		Field('creado','datetime'),
		)
db.post.autor.readable = False
db.post.autor.writable = False
db.post.autor.default = auth.user.id if auth.user else None
db.post.autor.requires = IS_NOT_EMPTY()

db.post.creado.readable = False
db.post.creado.writable = False
db.post.creado.default = request.now

db.post.puntos.readable = False
db.post.puntos.writable = False
db.post.puntos.default = 0

db.post.categoria.requires = IS_IN_DB(db, db.categoria.id, '%(nombre)s' )

db.define_table('comentario',
		Field('post', db.post),
		Field('autor', db.auth_user),
		Field('contenido', 'text')
		)
db.comentario.autor.readable = False
db.comentario.autor.writable = False
db.comentario.autor.requires = IS_IN_DB(db, db.auth_user.id, '%(username)s')

db.comentario.post.readable = False
db.comentario.post.writable = False
db.comentario.post.requires = IS_IN_DB(db, db.post.id, '%(titulo)s')
