
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='fluxrun',
    packages=setuptools.find_packages(),
    # packages=['dyco'],
    version='0.0.1',
    license='GNU General Public License v3 (GPLv3)',
    description='A Python package to convert binary files into other formats',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Lukas Hörtnagl',
    author_email='lukas.hoertnagl@usys.ethz.ch',
    url='https://gitlab.ethz.ch/holukas/bico-binary-converter',
    download_url='https://pypi.org/project/bico/',
    keywords=['ecosystem', 'eddy covariance', 'fluxes',
              'time series', 'binary', 'converter'],
    install_requires=['pandas', 'numpy', 'matplotlib'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
