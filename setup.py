# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    'pyramid',
    'pyramid_tm',
    'psycopg2',
    # "pymysql", 
    # 'pymssql', ## need freetds-dev及相关
    # 'redis',
    'SQLAlchemy',
    'transaction',
    'apscheduler',
    'pyramid_rpc',
    'zope.sqlalchemy',
    'numpy',
    'pandas',
    # 'tensorflow',
    'pyramid_chameleon',
    'pyramid_debugtoolbar',
    'waitress',
    ]

tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest',  # includes virtualenv
    'pytest-cov',
    ]

setup(name='Kitte',
      version='0.6',
      description='Kitte',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='NieMinMax',
      author_email='nie.minmax@gmail.com',
      url='https://github.com/NieMinMax/Kitte',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      extras_require={
          'testing': tests_require,
      },
      install_requires=requires,
      dependency_links=[
          # 'https://storage.googleapis.com/tensorflow/linux/cpu/tensorflow-0.9.0-cp27-none-linux_x86_64.whl',
          # 'https://storage.googleapis.com/tensorflow/linux/cpu/tensorflow-0.9.0-cp27-none-linux_x86_64.whl',
      ],
      entry_points="""\
      [paste.app_factory]
      main = kitte:main
      [console_scripts]
      initialize_kitte_db = kitte.scripts.initializedb:main
      """,
      )
