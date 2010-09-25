from setuptools import setup, find_packages

version = '0.2'

setup(
    name='collective.blueprint.usersandgroups',
    version=version,
    description="collective.transmogrifier blueprints for importing users \
                 and groups into plone",
    long_description=open("README.txt").read(),
    classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
    ],
    keywords='plone transmogrifier blueprint users groups',
    author='Rok Garbas',
    author_email='rok@garbas.si',
    url='',
    license='BSD',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['collective', 'collective.blueprint'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'collective.transmogrifier',
    ],
    extras_require = {
        'test': [
            'plone.app.testing',
        ]
    },
)
