from zope.interface import implements, classProvides
from collective.transmogrifier.interfaces import ISection, ISectionBlueprint
from Products.CMFCore.utils import getToolByName
from zope.app.component.hooks import getSite
from AccessControl.interfaces import IRoleManager
from plone.i18n.normalizer import idnormalizer
from Products.PlonePAS.interfaces.group import IGroupManagement

class CreateUser(object):
    """ """

    implements(ISection)
    classProvides(ISectionBlueprint)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context
        self.regtool = getToolByName(self.context, 'portal_registration')

    def __iter__(self):
        for item in self.previous:

            if '_password' not in item.keys() or \
               '_username' not in item.keys():
                yield item; continue

            if self.regtool.isMemberIdAllowed(item['_username']):
                self.regtool.addMember(item['_username'],
                                item['_password'].encode('utf-8'))
            yield item


class CreateGroup(object):
    """ """

    implements(ISection)
    classProvides(ISectionBlueprint)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context
        self.gtool = getToolByName(self.context, 'portal_groups')

    def __iter__(self):
        for item in self.previous:
            if item.get('_groupname', False):
                if '_properties' in item and \
                       not item['_properties'].get('title'):
                    item['_properties']['title'] = item['_groupname']
                item['_groupname'] = idnormalizer.normalize(item['_groupname'])
                self.gtool.addGroup(item['_groupname'])
            yield item


class UpdateUserProperties(object):
    """ """

    implements(ISection)
    classProvides(ISectionBlueprint)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context
        self.memtool = getToolByName(self.context, 'portal_membership')
        self.gtool = getToolByName(self.context, 'portal_groups')
        self.group_plugins = self.gtool._getPlugins()\
                             .listPlugins(IGroupManagement)
        self.portal = getSite()
        

    def __iter__(self):
        for item in self.previous:

            if '_username' in item.keys():
                member = self.memtool.getMemberById(item['_username'])
                if not member:
                    yield item; continue
                member.setMemberProperties(item['_properties'])

                # add member to group
                if item.get('_user_groups', False):
                    
                    for groupid in item['_user_groups']:
                        if groupid.startswith(u'group_'):
                            ## because group is prefixed by group
                            groupid = groupid[len(u'group_'):]
                        groupid = idnormalizer.normalize(groupid)
                        group = self.gtool.getGroupById(groupid)
                        ## because of postonly
                        if group:
                            for mid,  manager in self.group_plugins:
                                try:
                                    if manager\
                                       .addPrincipalToGroup(item['_username'],
                                                            group.getId()):
                                        
                                        break
                                except:
                                    pass
                            

                # setting global roles
                if item.get('_root_roles', False):
                    self.portal.acl_users.userFolderEditUser(
                                item['_username'],
                                None,
                                item['_root_roles'])

                # setting local roles
                if item.get('_local_roles', False):
                    try:
                        obj = self.portal.unrestrictedTraverse(item['_plone_site'])
                    except (AttributeError, KeyError):
                        pass
                    else:
                        if IRoleManager.providedBy(obj):
                            obj.manage_addLocalRoles(item['_username'], item['_local_roles'])
                            obj.reindexObjectSecurity()

            yield item


class UpdateGroupProperties(object):
    """ """

    implements(ISection)
    classProvides(ISectionBlueprint)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context
        self.gtool = getToolByName(self.context, 'portal_groups')
        self.portal = getSite()

    def __iter__(self):
        for item in self.previous:
            if not item.get('_groupname', False):
                yield item; continue
            group = self.gtool.getGroupById(item['_groupname'])
            if not group:
                yield item; continue

            if item.get('_root_group', False):
                self.gtool.editGroup(item['_groupname'],
                                    roles=item['_roles'])
            elif item.get('_roles', False):

                # setting local roles
                try:
                    obj = self.portal.unrestrictedTraverse(item['_plone_site'])
                except (AttributeError, KeyError):
                    pass
                else:
                    if IRoleManager.providedBy(obj):
                        obj.manage_addLocalRoles(item['_groupname'], item['_roles'])
                        obj.reindexObjectSecurity()
            if item.get('_group_groups', False):
                try:
                    self.gtool.editGroup(item['_groupname'],
                                    groups=item.get('_group_groups', []))
                except:
                    pass

            # With PlonePAS > 4.0b3, mutable_properties.enumerateUsers doesn't
            # return groups anymore, so it isn't possible to search a group
            # by its title stored in mutable_properties. Only the
            # title in source_groups is searched.
            # editGroup modify the title and description in source_groups
            # plugin, then it calls setGroupProperties(kw) which set the
            # properties on the mutable_properties plugin.
            if '_properties' in item:
                self.gtool.editGroup(item['_groupname'],
                                     **item['_properties'])
                
            yield item


class UpdateLdapGroups(object):
    """ """

    implements(ISection)
    classProvides(ISectionBlueprint)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context
        self.acl_users = getToolByName(self.context, 'acl_users')
        self.gtool = getToolByName(self.context, 'portal_groups')
        self.portal = getSite()
        self.group_plugins = self.gtool._getPlugins()\
                             .listPlugins(IGroupManagement)

    def __iter__(self):
        for item in self.previous:
            if not item.get('_data', False):
                yield item; continue
            if item.get('_type', None) != 'LdapUserFolder':
                yield item; continue
            for key in item['_data']:

                
                cn=key.split(',')[0][len('CN='):]
                users = self.acl_users.searchUsers(fullname=cn)
                for user in users:
                    
                    if user.get('dn','') == key or cn=='lecteur':
                        import pdb;pdb.set_trace();
                        self.acl_users.userFolderEditUser(
                            user['id'], None, item['_data'][key]['roles']
                            )
                        for groupid in item['_data'][key]['groups']:
                            if groupid.startswith(u'group_'):
                                groupid = groupid[len(u'group_'):]
                            groupid = idnormalizer.normalize(groupid)  
                            for mid,  manager in self.group_plugins:
                                try:
                                    if manager\
                                       .addPrincipalToGroup(user['id'],
                                                            groupid):
                                        break
                                except:
                                    pass
