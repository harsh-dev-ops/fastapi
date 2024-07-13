from sqlalchemy import create_engine, Column, Integer, Unicode, ForeignKey
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy

# Configure test data SA
engine = create_engine(u'sqlite:///:memory:', echo=False)
session = scoped_session(sessionmaker(bind=engine, autoflush=False))
Base = declarative_base()

class _BaseMixin(object):
    """
    A helper mixin class to set properties on object creation.

    Also provides a convenient default __repr__() function, but be aware that
    also relationships are printed, which might result in loading the relation
    objects from the database
    """
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return "<%s(%s)>" % (self.__class__.__name__,
            ', '.join('%s=%r' % (k, self.__dict__[k])
                      for k in sorted(self.__dict__)
                      if '_' != k[0]
                      #if '_sa_' != k[:4] and '_backref_' != k[:9]
                      )
            )


# relation creator factory functions
def _creator_gr(group, role):
    res = UserGroup(group=group, role=role)
    return res
def _creator_ur(user, role):
    res = UserGroup(user=user, role=role)
    return res

##############################################################################
# Object Model
##############################################################################
class Role(Base, _BaseMixin):
    __tablename__ = 'roles'
    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(16), unique=True)
    # relations
    usergroup = relationship("UserGroup", backref='role')

class User(Base, _BaseMixin):
    __tablename__ = 'users'
    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(16), unique=True)
    # relations
    _rel_usergroup = relationship("UserGroup", collection_class=attribute_mapped_collection('group'),
                                  cascade='all,delete-orphan',
                                  backref='user',
                                  )
    groups = association_proxy('_rel_usergroup', 'role', creator=_creator_gr)

class Group(Base, _BaseMixin):
    __tablename__ = 'groups'
    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(16), unique=True)
    # relations
    _rel_usergroup = relationship("UserGroup", collection_class=attribute_mapped_collection('user'),
                                  cascade='all,delete-orphan',
                                  backref='group',
                                  )
    users = association_proxy('_rel_usergroup', 'role', creator=_creator_ur)

class UserGroup(Base, _BaseMixin):
    __tablename__ = 'user_group'
    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    group_id = Column(Integer, ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    # relations
    # (all backrefs)



##############################################################################
# TESTS (showing usages)
#
# Requirements:
#  - list all groups of the user: user.groups (use keys)
#  - list all users of the group: group.users (use keys)
#  - get all users ordered (grouped) by group with the role title
##############################################################################

def _requirement_get_user_groups(user):
    return user.groups.keys()

def _requirement_get_group_users(group):
    return group.users.keys()

def _requirement_get_all_users_by_group_with_role():
    qry = session.query(Group).order_by(Group.name)
    res = []
    for g in qry.all():
        for u, r in sorted(g.users.items()):
            value = (g.name, u.name, r.name)
            res.append(value)
    return res

def _test_all_requirements():
    print '--requirement: all-ordered:'
    for v in _requirement_get_all_users_by_group_with_role():
        print v

    print '--requirement: user-groups:'
    for v in session.query(User).order_by(User.id):
        print v, " has groups: ",  _requirement_get_user_groups(v)

    print '--requirement: group-users:'
    for v in session.query(Group).order_by(Group.id):
        print v, " has users: ",  _requirement_get_group_users(v)

# create db schema
Base.metadata.create_all(engine)

##############################################################################
# CREATE TEST DATA
##############################################################################

# create entities
u_peter = User(name='u_Peter')
u_sonja = User(name='u_Sonja')
g_sales = Group(name='g_Sales')
g_wales = Group(name='g_Wales')
r_super = Role(name='r_Super')
r_minor = Role(name='r_Minor')

# helper functions
def _get_entity(entity, name):
    return session.query(entity).filter_by(name=name).one()
def get_user(name):
    return _get_entity(User, name)
def get_group(name):
    return _get_entity(Group, name)
def _checkpoint():
    session.commit()
    session.expunge_all()
    _test_all_requirements()
    session.expunge_all()
    print '-' * 80


# test: **ADD**
u_peter.groups[g_wales] = r_minor # add
g_wales.users[u_sonja] = r_super # add
g_sales.users[u_peter] = r_minor # add
session.add(g_wales)
#session.add(g_sales)
_checkpoint()

# test: **UPDATE**
u_peter = get_user('u_Peter')
assert u_peter.name == 'u_Peter' and len(u_peter.groups) == 2
assert len(u_peter.groups) == 2
g_wales = get_group('g_Wales')
g_wales.users[u_peter] = r_super # update
_checkpoint()

# test: **DELETE**
u_peter = get_user('u_Peter')
assert u_peter.name == 'u_Peter' and len(u_peter.groups) == 2
g_wales = get_group('g_Wales')
del u_peter.groups[g_wales] # delete
_checkpoint()