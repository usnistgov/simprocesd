from setuptools import find_packages, setup

source_code_url = 'https://github.com/usnistgov/simantha'
with open('README.md', 'r') as f:
    long_description = f.read().split('\n')
long_description = '\n'.join(long_description[:10])
long_description = long_description + \
        f'\nSee the project\'s [GitHub page]({source_code_url}) for more information.'

setup(
    name = 'sim-procesd',
    version = '0.1.4',
    author = 'Serghei Drozdov',
    author_email = 'serghei.drozdov@nist.gov',
    description = 'Discreet event simulator for manufacturing systems.',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    project_urls = {
        'Source Code': source_code_url
    },
    license = 'US Government Open Source',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.9',
        'Intended Audience :: Manufacturing',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ],
    packages = find_packages(exclude = ['simprocesd.tests',
                                        'simprocesd.tests.*']),
    install_requires = ['matplotlib', 'numpy', 'scipy']
)
