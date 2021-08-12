# SETUPTOOLS INSTALL DOES NOT WORK AT THE MOMENT

# https://chriswarrick.com/blog/2014/09/15/python-apps-the-right-way-entry_points-and-scripts/
# https://stackoverflow.com/questions/3542119/create-launchable-gui-script-from-python-setuptools-without-console-window


import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='fluxrun',
    entry_points={"console_scripts": ["fluxrun = fluxrun.__main__:main"]},
    # entry_points={"gui_scripts": ["fluxrun = fluxrun.__main__:main"]},
    packages=setuptools.find_packages(),
    version='1.0',
    license='GNU General Public License v3 (GPLv3)',
    description='Python wrapper for EddyPro flux calculations',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Lukas Hörtnagl',
    author_email='holukas@ethz.ch',
    url='https://gitlab.ethz.ch/holukas/bico-binary-converter',
    download_url='https://pypi.org/project/bico/',
    keywords=['ecosystem', 'eddy covariance', 'fluxes',
              'time series', 'binary', 'converter'],
    install_requires=['pandas', 'matplotlib',
                      'PyQt5'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
    ],
    python_requires='==3.8.5',
)
