import re
from setuptools import setup, find_packages

with open('README.md') as readme:
    long_description = readme.read()


def get_version(filename='canaveral/__init__.py'):
    """ Extract version information stored as a tuple in source code """
    version = ''
    with open(filename, 'r') as fp:
        for line in fp:
            m = re.search("__version__ = '(.*)'", line)
            if m is not None:
                version = m.group(1)
                break
    return version


# What packages are required for this module to be executed?
REQUIRED = open('requirements.txt', 'r').read().splitlines()

setup(
    name="canaveral",
    version=get_version(),

    # py_modules=["canaveral"],
    package_dir={'canaveral': 'canaveral'},
    # packages=['canaveral'] + find_packages('canaveral'),
    packages=['canaveral', 'canaveral.qtkeybind', 'canaveral.qtkeybind.win', 'canaveral.qtkeybind.x11'],
    package_data={'canaveral': ['resources/*.png', 'resources/*.ico']},
    install_requires=REQUIRED,
    entry_points={
        'console_scripts': ['canaveral-console=canaveral.main:run'],
        'gui_scripts': ['canaveral=canaveral.main:run'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Environment :: Win32 (MS Windows)',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Utilities',
    ],

    # metadata for upload to PyPI
    author="Josh Burnett",
    author_email="github@burnettsonline.org",
    description="Quickly find and open applications and files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="canaveral launcher launch utility keyboard",
    url="https://github.com/joshburnett/canaveral",
    platforms=['windows'],
)
