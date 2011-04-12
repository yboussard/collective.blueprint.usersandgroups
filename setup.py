from setuptools import setup, find_packages
import os

version = '0.2.0'

setup(name='collective.blueprint.usersandgroups',
      version=version,
      description="transmogrifier blueprints for importing users and groups into plone",
      long_description=open("README.txt").read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='plone transmogrifier blueprint user group',
      author='garbas + yboussard',
      author_email='yboussard@alterway.fr',
      url='http://svn.plone.org/svn/collective/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective', 'collective.blueprint'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'collective.transmogrifier',
      ],
      )
