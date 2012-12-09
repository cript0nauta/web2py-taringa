# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

MAX_POSTS = 5 # Posts a mostrar en el index
TOP_POSTS = 3 # Posts a mostrar en la sección tops

def tops():
		""" Retorna los top posts y usuarios """
		posts = db(db.post.id>0).select(orderby=~db.post.puntos)[:TOP_POSTS]

		users = {}
		for u in db().select(db.auth_user.ALL):
				p = sum([p.puntos for p in u.post.select()])
				users[u.username] = p
		users =  sorted(users.items(), key = lambda k: k[1], reverse = True)[:TOP_POSTS]
		return dict(posts=posts, users=users)

def index():
	if len(request.args):
		# Le pasamos una categoria
		categoria = db(db.categoria.identifier==request.args[0]).select()
		categoria = categoria[0] if categoria else None
		if not categoria:
			return T('Categoría desconocida')
	else:
		categoria = None
	categorias = db().select(db.categoria.ALL)
	d = db(db.post.categoria==categoria.id) if categoria else db()
	p = d.select(db.post.ALL, orderby=~db.post.id)[:MAX_POSTS]
	return dict(categorias = categorias,
			posts = p,
			tops = tops())

def post():
	if len(request.args)==1:
		post = db(db.post.id==request.args[0]).select()
		post = post[0] if post else None
		if not post:
			raise HTTP(404)
		if auth.user:
			user = db(db.auth_user.id==auth.user.id).select()[0]
			inputs = [SPAN(INPUT(_type='radio', 
						_name='puntos', _value=i,
						requires = IS_INT_IN_RANGE(1,user.puntos+1)), 
						i,XML('<br>')) \
					for i in range(1,user.puntos + 1)]
			if not inputs:
					inputs.append(T('No te quedan puntos para dar hoy'))
			else:
					inputs.append(INPUT(_type='submit', _value=T('Puntuar')))
			puntuar = FORM(*inputs)
			if puntuar.accepts(request.vars, session):
					response.flash = T('Puntuaste el post con %s puntos',\
									request.vars.puntos)
					puntos_post = post.puntos + int(request.vars.puntos)
					db(db.post.id==post.id).update(puntos = puntos_post)

					puntos_usr = user.puntos - int(request.vars.puntos)
					db(db.auth_user.id==auth.user.id).update(puntos=puntos_usr)

					redirect(URL(f='post',args=post.id))
			elif puntuar.errors:
					response.flash = T('Datos incorrectos')
		else:
			puntuar = None
		return dict(post=post, puntuar=puntuar)
	else:
		raise HTTP(404)

def profile():
		""" Ver el perfil de algún usuario """
		user = db(db.auth_user.username==request.args(0)).select()
		if not user:
				response.flash='El perfil no existe'
				return dict(user=None)
		user = user[0]
		posts = db(db.post.autor==user.id).select()
		puntos = sum([post.puntos for post in posts])
		return dict(user=user, posts=posts, puntos=puntos)

@auth.requires_login()
def newpost():
	form = crud.create(db.post)
	return dict(form=form)

def edit():
	""" Editar un post """
	post = db(db.post.id == request.args(0)).select()
	if post:
		form = crud.update(db.post, post[0].id, \
				next=URL(f='post',args=post[0].id))
		return dict(form = form)
	else:
		raise HTTP(404)

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
