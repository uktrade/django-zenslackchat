from setuptools import setup

with open('requirements.txt') as fd:
    install_requires = fd.readlines()

with open('README.rst') as fd:
    long_description = fd.read()

setup(
    name='zenslackchat',
    zip_safe=False,
    version='1.0.0',
    author='DIT',
    author_email='',
    description='Helpdesk support using a slack chat bot and integration into zendesk.',
    long_description=long_description,
    include_package_data=True,
    keywords='web services',
    install_requires=install_requires,
)
