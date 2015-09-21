from setuptools import setup

setup(
    name='elasticsearch-runner',
    version='0.1',
    packages=['resources', 'elasticsearch_runner', 'elasticsearch_runner.test'],
    url='https://bitbucket.org/comperio/comperio-text-analytics',
    license='For internal use only.',
    author='Andre Lynum',
    author_email='andre.lynum@comperiosearch.com',
    description='Lightweight runner for transient Elasticsearch instances, f.ex for testing.',
    install_requires=['PyYAML', 'elasticsearch', 'requests', 'psutil', 'lxml'],
    package_data={'resources': ['embedded_elasticsearch.yml']}
)
