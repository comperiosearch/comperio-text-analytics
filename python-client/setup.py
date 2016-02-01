from setuptools import setup

setup(
    name='es_text_analytics',
    version='0.1',
    packages=['es_text_analytics', 'es_text_analytics.test'],
    url='https://bitbucket.org/comperio/comperio-text-analytics',
    license='For internal use only.',
    author='Andre Lynum',
    author_email='andre.lynum@comperiosearch.com',
    description='es text analytics.',
    install_requires=['elasticsearch', 'requests', 'psutil',  'textblob', 'nltk',  'gensim', 'uniseg'],
    dependency_links=['git+ssh://git@github.com/comperiosearch/python-elasticsearch-runner']

)
