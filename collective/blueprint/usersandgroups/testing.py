from plone.testing import Layer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting, FunctionalTesting

class BlueprintUsersAndGroups(Layer):
    default_bases = (PLONE_FIXTURE,)


BLUEPRINT_USERSANDGROUPS_FIXTURE = BlueprintUsersAndGroups()
BLUEPRINT_USERSANDGROUPS_INTEGRATION_TESTING = IntegrationTesting(
        bases=(BLUEPRINT_USERSANDGROUPS_FIXTURE,),
        name="BlueprintUsersAndGroups:Integration")
BLUEPRINT_USERSANDGROUPS_FUNCTIONAL_TESTING = FunctionalTesting(
        bases=(BLUEPRINT_USERSANDGROUPS_FIXTURE,),
        name="BlueprintUsersAndGroups:Functional")

