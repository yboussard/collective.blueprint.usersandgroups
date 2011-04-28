import os
import simplejson
from datetime import datetime

from App.config import getConfiguration


COUNTER = 1

UTEMP = os.path.join(getConfiguration().instancehome, 'var',
                     'exportuser-%s' % datetime.today()\
                     .strftime('%Y-%m-%d-%H-%M-%S'))

GTEMP = os.path.join(getConfiguration().instancehome, 'var',
                     'exportgroup-%s' % datetime.today()\
                     .strftime('%Y-%m-%d-%H-%M-%S'))
LTEMP = os.path.join(getConfiguration().instancehome, 'var',
                     'exportldap-%s' % datetime.today()\
                     .strftime('%Y-%m-%d-%H-%M-%S'))


for path in (UTEMP, GTEMP, LTEMP):
    if not os.path.isdir(path):
        os.makedirs(path)


GROUPS = {}
GROUP_NAMES = {}
USERS = {}

def export(self):
    get_users_and_groups([self], 1)
    # it's stupid to do that
    #get_users_and_groups(walk_all(self), 0)
    store_users_and_groups()
    get_ldapuser_folder(self)
    return 'OK'

def walk_all(folder):
    for item_id in folder.objectIds():
        item = folder[item_id]
        yield item
        if getattr(item, 'objectIds', None) and \
           item.objectIds():
            for subitem in walk_all(item):
                yield subitem



def get_ldapuser_folder(context):
    global COUNTER
    acl_users = context.acl_users
    
    charset = context.portal_properties.site_properties.default_charset
    for x in acl_users.objectValues(['GRUFUsers',]):
        if 'acl_users' in x.objectIds() \
               and x['acl_users'].meta_type == 'LDAPUserFolder':
            ## we have an candidates
            obj = x['acl_users']
            json = {}
            json['_config'] = {}
            json['_type'] = 'LdapUserFolder'
            ## first import configuration
            for x in ('_rdnattr',
                      '_roles',
                       'groups_scope',
                       '_binduid_usage',
                       'groups_base',
                       '_binduid',
                       '_bindpwd',
                       '_authenticated_timeout',
                       'users_base',
                       'read_only',
                       '_uid_attr',
                       'title',
                       '_pwd_encryption',
                       '_local_groups',
                       '_user_objclasses',
                       '_login_attr',
                       '_additional_groups',
                       'users_scope',
                      '_ldapschema'):
                json['_config'][x] = getattr(obj,x)
            ## configuration of server
            json['_config']['_servers'] = obj._delegate._servers
            json['_data'] = {}
            
            for x,y in obj._groups_store.iteritems():
                ##  ('CN=toto,OU=Pollux Prod', ['Member', 'group_Groupe_BioCom'])]
                key = x.decode(charset,'ignore')
                                
                
                json['_data'][key] = {'roles':[], 'groups':[]}
                for rorg in y:
                    rorg = rorg.decode(charset,'ignore')
                    if rorg.startswith(u'group_'):
                        ## its a group
                        json['_data'][key]['groups'].append(rorg)
                    else:
                        if rorg not in json['_data'][key]['roles']:
                            json['_data'][key]['roles'].append(rorg)
            
            write(json, LTEMP)
            COUNTER +=1
            
            

def get_users_and_groups(items, root):
    global GROUPS
    global GROUP_NAMES
    global USERS

    for item in items:
        if item.__class__.__name__ == 'PloneSite' and \
                        not item.getId().startswith('copy_of'):
            charset = item.portal_properties.site_properties.default_charset
            properties = []
            if getattr(item, 'portal_groups', False):
                gtool = item.portal_groups
                if getattr(item, 'portal_groupdata', False):
                    gdtool = item.portal_groupdata
                    for pid in gdtool.propertyIds():
                        typ = gdtool.getPropertyType(pid)
                        properties.append((pid, typ))
                for group in item.portal_groups.listGroups():
                    group_name = str(group.getUserName())
                    if group.getUserName() in GROUPS.keys():
                        GROUP_NAMES[group_name] = 1
                        group_name = group_name+'_'+item.getId()
                        GROUP_NAMES[group_name] = 0
                    else:
                        GROUP_NAMES[group_name] = 0
                    group_data = {}
                    group_data['_groupname'] = group_name
                    roles = group.getRoles()
                    local_roles = item.__ac_local_roles__
                    if local_roles.get(group_name, False):
                        roles += tuple(local_roles[group_name])
                    ## set type is not available for python2.3
                    ignoredset = ('Authenticated', 'Member')
                    roles = [x for x in roles if x not in ignoredset]
                    group_data['_roles'] = roles
                    group_data['_plone_site'] = '/'.join(item.getPhysicalPath())
                    group_data['_properties'] = {}
                    group_data['_root_group'] = root
                    for pid, typ in properties:
                        val = group.getProperty(pid)
                        if typ in ('string', 'text'):
                            if getattr(val, 'decode', False):
                                try:
                                    val = val.decode(charset, 'ignore')
                                except UnicodeEncodeError:
                                    val = unicode(val)
                            else:
                                val = unicode(val)
                        group_data['_properties'][pid] = val
                    if getattr(group, 'getGroups', False):
                        groups = group.getGroup().getGroups()
                        group_data['_group_groups'] = groups
                    GROUPS[group_name] = group_data
            if not getattr(item, 'portal_membership', False):
                continue
            properties = []
            if  getattr(item, 'portal_memberdata', False):
                mdtool = item.portal_memberdata
                for pid in mdtool.propertyIds():
                    typ = mdtool.getPropertyType(pid)
                    properties.append((pid, typ))
            for member in item.portal_membership.listMembers():
                user_data = {}
                user_name = str(member.getUserName())
                user_data['_username'] = user_name
                user_data['_password'] = str(member.getUser()._getPassword())
                user_data['_root_user'] = root
                user_data['_root_roles'] = []
                user_data['_local_roles'] = []
                if root:
                    user_data['_root_roles'] = member.getRoles()
                else:
                    roles = member.getRoles()
                    local_roles = item.__ac_local_roles__
                    if local_roles.get(user_name, False):
                        roles += tuple(local_roles[user_name])
                    ignoredset = ('Authenticated', 'Member')
                    roles = [x for x in roles if x not in ignoredset]
                    #ignoredset = set(['Authenticated', 'Member'])
                    #roles = list(set(roles).difference(ignoredset))
                    user_data['_local_roles'] = roles
                user_data['_user_groups'] = []
                user_data['_plone_site'] = '/'.join(item.getPhysicalPath())
                if getattr(member, 'getGroups', False):
                    user_data['_user_groups'] = member.getGroups()
                user_data['_properties'] = {}
                for pid, typ in properties:
                    val = member.getProperty(pid)
                    if typ in ('string', 'text'):
                        if getattr(val, 'decode', False):
                            try:
                                val = val.decode(charset, 'ignore')
                            except UnicodeEncodeError:
                                val = unicode(val)
                        else:
                            val = unicode(val)
                    if typ == 'date':
                        val = str(val)
                    user_data['_properties'][pid] = val
                USERS[user_name] = user_data

def store_users_and_groups():
    global GROUPS
    global USERS
    global COUNTER
    for group_name, group_data in GROUPS.items():
        
        group = fix_group_names((group_data['_groupname'],), group_data)[0]
        group_data['_groupname'] = group
        ### _group_groups is prefixed by group_ 
        groups = fix_group_names( group_data['_group_groups'] ,
                                  group_data)
        group_data['_group_groups'] = groups
        write(group_data, GTEMP)
        print '   |--> '+str(COUNTER)+' - '+str(group_data['_groupname'])+' IN: '+group_data['_plone_site']
        COUNTER += 1
    COUNTER = 0
    for user_name, user_data in USERS.items():
        
        groups = fix_group_names(user_data['_user_groups'], user_data)
        user_data['_user_groups'] = groups
        write(user_data, UTEMP)
        COUNTER += 1
        print '   |--> '+str(COUNTER)+' - '+str(user_data['_username'])+' IN: '+user_data['_plone_site']
    print '----------------------------  --------------------------------------'

def fix_group_names(groupnames, data):
    groups = []
    for group in groupnames:
        rgroup = group.replace(' ', '_').replace('-', '_')
        try:
            ### in case of _group_groups or of _user_groups
            if group.startswith('group_'):
                group = group[len('group_'):]
            if GROUP_NAMES[group]:
                groups.append(rgroup+'_'+data['_plone_site'].strip('/').split('/')[-1])
            else:
                groups.append(rgroup)
        except:
            import pdb;pdb.set_trace();
            pass
            
    return groups


def write(item, temp):
    SUBTEMP = str(COUNTER/1000) # 1000 files per folder
    if not os.path.isdir(os.path.join(temp, SUBTEMP)):
        os.mkdir(os.path.join(temp, SUBTEMP))

    f = open(os.path.join(temp, SUBTEMP, str(COUNTER % 1000)+'.json'), 'wb')
    simplejson.dump(item, f, indent=4)
    f.close()
