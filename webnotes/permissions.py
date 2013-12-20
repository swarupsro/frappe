# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import webnotes
from webnotes import _, msgprint, _dict
from webnotes.utils import cint

def check_admin_or_system_manager():
	if ("System Manager" not in webnotes.get_roles()) and \
	 	(webnotes.session.user!="Administrator"):
		msgprint("Only Allowed for Role System Manager or Administrator", raise_exception=True)
		
def has_permission(doctype, ptype="read", refdoc=None, verbose=True):
	"""check if user has permission"""
	if webnotes.conn.get_value("DocType", doctype, "istable")==1:
		return True
	
	meta = webnotes.get_doctype(doctype)
	
	if ptype=="submit" and not cint(meta[0].is_submittable):
		return False
	
	if ptype=="import" and not cint(meta[0].allow_import):
		return False
	
	if webnotes.session.user=="Administrator":
		return True
	
	# get user permissions
	perms = get_user_perms(meta, ptype)
	
	if not perms:
		return False
	elif refdoc:
		if isinstance(refdoc, basestring):
			refdoc = webnotes.doc(meta[0].name, refdoc)
		
		if (has_only_permitted_data(meta, refdoc, verbose=verbose) and has_match(perms, refdoc)):
			return True
		else:
			return False
	else:
		return True
		
def get_user_perms(meta, ptype, user=None):
	user_roles = webnotes.get_roles(user)
	
	return [p for p in meta.get({"doctype": "DocPerm"})
			if cint(p.get(ptype))==1 and cint(p.permlevel)==0 and (p.role=="All" or p.role in user_roles)]

def has_only_permitted_data(meta, refdoc, verbose=True):
	from webnotes.defaults import get_restrictions
	restrictions = get_restrictions()
	if not restrictions:
		return True
	
	fields_to_check = meta.get_restricted_fields(restrictions.keys())
	
	has_restricted_data = False
	for df in fields_to_check:
		if refdoc.get(df.fieldname) and refdoc.get(df.fieldname) not in restrictions[df.options]:
			if verbose:
				msg = "{not_allowed}: {doctype} {having} {label} = {value}".format(
					not_allowed=_("Sorry, you are not allowed to access"), doctype=_(df.options),
					having=_("having"), label=_(df.label), value=refdoc.get(df.fieldname))
			
				if refdoc.parentfield:
					msg = "{doctype}, {row} #{idx}, ".format(doctype=_(refdoc.doctype),
						row=_("Row"), idx=refdoc.idx) + msg
			
				msgprint(msg)
			
			has_restricted_data = True
	
	# check all restrictions before returning
	return False if has_restricted_data else True

def has_match(perms, refdoc):
	"""check owner match (if exists)"""
	for p in perms:
		if p.get("match")=="owner":
			if refdoc.get("owner")==webnotes.local.session.user:
				# owner matches :)
				return True
		else:
			# found a permission without owner match :)
			return True
	
	# no match :(
	return False
	
def can_restrict_user(user, doctype, docname=None):
	if not can_restrict(doctype, docname):
		return False
		
	meta = webnotes.get_doctype(doctype)
	
	# check if target user does not have restrict permission
	if has_only_non_restrict_role(meta, user):
		return True
	
	return False
	
def can_restrict(doctype, docname=None):
	# System Manager can always restrict
	if "System Manager" in webnotes.get_roles():
		return True

	meta = webnotes.get_doctype(doctype)
	
	# check if current user has read permission for docname
	if docname and not has_permission(doctype, "read", docname):
		return False

	# check if current user has a role with restrict permission
	if not has_restrict_permission(meta):
		return False
	
	return True
	
def has_restrict_permission(meta=None, user=None):
	return any((perm for perm in get_user_perms(meta, "read", user)
		if cint(perm.restrict)==1))
	
def has_only_non_restrict_role(meta, user):
	# check if target user does not have restrict permission
	if has_restrict_permission(meta, user):
		return False
	
	# and has non-restrict role
	return any((perm for perm in get_user_perms(meta, "read", user)
		if cint(perm.restrict)==0))

def can_import(doctype, raise_exception=False):
	if not ("System Manager" in webnotes.get_roles() or has_permission(doctype, "import")):
		if raise_exception:
			raise webnotes.PermissionError("You are not allowed to import: {doctype}".format(doctype=doctype))
		else:
			return False
	return True
	
def can_export(doctype, raise_exception=False):
	if not ("System Manager" in webnotes.get_roles() or has_permission(doctype, "export")):
		if raise_exception:
			raise webnotes.PermissionError("You are not allowed to export: {doctype}".format(doctype=doctype))
		else:
			return False
	return True
	