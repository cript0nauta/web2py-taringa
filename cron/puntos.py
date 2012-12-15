#!/usr/bin/env python
#-*- coding: utf-8 -*-

#db(db.auth_user.id>0).update(puntos=10)

for user in db(db.auth_user.id>0).select():
		if db.auth_user.rango(user.id) == T('New Full User'):
				# Usuario NFU, tiene 10 puntos para dar
				db(db.auth_user.id==user.id).update(puntos=10)
		else:
				# Usuario novato, tiene 3 puntos para dar
				db(db.auth_user.id==user.id).update(puntos=3)
