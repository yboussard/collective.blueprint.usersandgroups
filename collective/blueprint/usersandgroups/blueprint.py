from zope.interface import implements, classProvides
from collective.transmogrifier.interfaces import ISection, ISectionBlueprint
from Products.CMFCore.utils import getToolByName
from zope.app.component.hooks import getSite
from AccessControl.interfaces import IRoleManager


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

            if '_user_password' not in item.keys() or \
               '_user_name' not in item.keys():
                yield item; continue

            if self.regtool.isMemberIdAllowed(item['_user_name']):
                self.regtool.addMember(item['_user_name'],
                                item['_user_password'].encode('utf-8'))
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
            if item.get('_group_name', False):
                self.gtool.addGroup(item['_group_name'])
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
        self.portal = getSite()

    def __iter__(self):
        for item in self.previous:

            if '_user_name' in item.keys():
                member = self.memtool.getMemberById(item['_user_name'])
                if not member:
                    yield item; continue
                member.setMemberProperties(item['_user_properties'])

                # add member to group
                if item.get('_user_groups', False):
                    for groupid in item['_user_groups']:
                        group = self.gtool.getGroupById(groupid)
                        if group:
                            group.addMember(item['_user_name'])

                # setting global roles
                if item.get('_user_global_roles', False):
                    self.portal.acl_users.userFolderEditUser(
                                item['_user_name'],
                                None,
                                item['_user_global_roles'])

                # setting local roles
                if item.get('_user_local_roles', False):
                    for path, role in item['_user_local_roles']:
                        try:
                            item_obj = self.portal.unrestrictedTraverse(path)
                        except (AttributeError, KeyError):
                            pass
                        else:
                            if IRoleManager.providedBy(item_obj):
                                item_obj.manage_addLocalRoles(
                                        item['_user_name'],
                                        item['_user_local_roles'])
                                item_obj.reindexObjectSecurity()

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
            if not item.get('_group_name', False):
                yield item; continue

            group = self.gtool.getGroupById(item['_group_name'])
            if not group:
                yield item; continue

            # setting group properties
            if item.get('_group_properties', False):
                group.setGroupProperties(item['_group_properties'])

            # setting groups of group
            if item.get('_group_groups', False):
                self.gtool.editGroup(item['_group_name'],
                                     groups=item.get('_group_groups', []))

            # setting global roles
            if item.get('_group_global_roles', False):
                self.gtool.editGroup(
                        item['_group_name'],
                        roles=item['_group_roles'])

            # setting local roles
            elif item.get('_group_roles', False):
                for path, role in item['_user_local_roles']:
                    try:
                        item_obj = self.portal.unrestrictedTraverse(path)
                    except (AttributeError, KeyError):
                        pass
                    else:
                        if IRoleManager.providedBy(item_obj):
                            item_obj.manage_addLocalRoles(
                                    item['_group_name'],
                                    item['_user_local_roles'])
                            item_obj.reindexObjectSecurity()

            yield item
