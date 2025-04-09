# Changelog

![](images/logo_FLUXRUN1_256px.png)

## v2.0.0 | XX Apr 2025

### Introducing v2.0.0

`fluxrun` has been updated to version 2.

`fluxrun` is a Python wrapper for EddyPro to calculate EC ecosystem fluxes from raw data files.

This version enhances its usability for a wider range of eddy covariance (EC) sites beyond
the [ETH Grassland Sciences group](https://gl.ethz.ch/).

[//]: # (<IMAGE>)

`fluxrun` can be executed using the GUI or directly from the command line interface.

`fluxrun` was created as a wrapper around EddyPro. This means that the flux calculations are done by EddyPro, but
`fluxrun` adds some functionality, e.g.:

- `fluxrun` automatically creates an output folder structure, including run ID.
- The log output from EddyPro (together with other output from `fluxrun`) is stored to a log file.
- There is an additional log file storing warnings and errors.
- `fluxrun` can be executed in parallel, e.g. when calculating fluxes for multiple years `fluxrun` makes it a bit easier
  to run them all at once. Parallelization is not included by default (at the moment), but using the command-line
  interface multiple instances of `fluxrun` can be started quickly. Each started instance gets its own output folder and
  folder structure, including a unique run ID.
- Input files are validated to make sure columns contain numeric data only. Non-numeric data are converted to `-9999`.
- `fluxrun` can create several plots during processing: raw data availability, raw data aggregates and summary plots of
  all variables in EddyPro's `_full_output_` file.
- In case compressed files are used (`.gz`), the files are automatically uncompressed (text format) before processing.
  After processing,in case the uncompressed files are no longer needed, they can be automatically deleted. Raw data eddy
  covariance files can be selected from a folder. Files are handled differently Depending on the file extension. If the
  files have the file extension `.gz`, they are uncompressed before further processing. Files need to be text-based,
  e.g. CSV files, but they can be compressed as `.gz`.

#### Installation

Installation is currently far from perfect, but here we go:

Using [miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install#quickstart-install-instructions):

- Create conda environment with required Python version: `conda create -n fluxrun-env python=3.11`
- Activate the created environment: `conda activate fluxrun-env`
- Now check the fluxrun releases [here](https://github.com/holukas/fluxrun/releases) and decide which version to use
- Spot the `.tar.gz` file of the desired fluxrun version and use it to directly install from the GitHub repo via pip:
  `pip install https://github.com/holukas/fluxrun/archive/refs/tags/v2.0.0.tar.gz`
- Now all required dependencies are installed in the environment `fluxrun-env`
- Spot the `.zip` file of the desired fluxrun version and download it from GitHub. Use the same version as for the
  `.tar.gz` file: https://github.com/holukas/fluxrun/archive/refs/tags/v2.0.0.zip
- Unzip the zip file to a folder, e.g. `C:\fluxrun-2.0.0`
- Start GUI: `python C:\fluxrun-2.0.0\fluxrun main.py -g`
- Start processing with CLI: `python C:\fluxrun-2.0.0\fluxrun main.py -f C:\my_project -d 10`. In this case, the
  folder `C:\my_project` needs to contain the `.eddypro` settings file that contains the flux processing settings for
  EddyPro. `fluxrun` will search for a `.metadata` file of the same name in the same folder as the `.eddypro` file. For
  example, if the settings file is named `my_settings.eddypro`, then `fluxrun` needs a metadata file with the name
  `my_settings.metadata` in the same folder. The parameter `-d 10` means that only fluxes for the last 10 days are
  calculted. This can be used to automatically calculate fluxes.

#### Description of GUI settings

##### Raw Data Files

- `Select raw data source folder (ASCII)`
- `File name ID`  (default: SITE_yyyymmddHHMM.csv.gz)
- `Header format`
- `Start`
- `End`
- `Plots`
  - `Availability (raw data)`
  - `Aggregates (raw data)`

##### Flux Processing Settings

- `Run flux calculation using EddyPro`
- `Select EddyPro processing file (*.eddypro)`

##### Output

- `Select output folder`
- `Output folder name prefix`
- `Plots`:
  - `Summary (flux processing)`

##### After Processing

- `Delete uncompressed raw data ASCII after processing`

- Raw Data Select source folder with EC raw data files
- Define file name ID. The file name needs to contain datetime info, it needs info about the year, month, day, hours and
  minutes.
- Then the header format is important, how many header rows are in the raw data files
- Define a start and end date for processing, files outside this range will be ignored
- Then there are options to plot data availablility (based on the datetime info in the filenames) and aggregates of the
  raw data
-
- Plots can be generated using the `_full_output_` file from the EddyPro output. Every variable is plotted.
- Then select an output folder, `fluxrun` creates an output folder with the defined prefix in this location
- After processing, `fluxrun` can delete the uncompressed ASCII files. The uncompressed files are needed for flux
  calculations, but unless there is a desire to store the uncompressed files they are no longer needed.

### Other changes

- Now using PyQt6 for GUI
- Updated code for PyQt6
- Fixed bug in pandas `.pivot()` method, small issue due to the updated pandas version
- `diive` is now using Python version `3.11` upwards
- Updated environment, poetry `pyproject.toml` file now has the currently used structure
- Added key shortcut to start processing ("Ctrl+R")
- Added key shortcut save settings ("Ctrl+S")
- Now always using forward slashes for paths

## v1.4.1 | 27 Mar 2024

- Added new sites `CH-FOR`, `CH-HON` and `CH-TAN` in site selection menu
- Now showing all sites when clicking on site selection drop-down menu
- Added info about default setting in GUI: `Date/Time Format In File Name (default: yyyymmddHHMM)`
- Updated links in sidebar to GitHub locations

## v1.4.0 | 27 Feb 2024

- Added: it is now possible to give a specific file extension in the GUI
  setting `Raw Data: File Settings` > `Date/Time Format In File name`. In case no file extension is given, `fluxrun`
  assumes `.csv` as the default file extension.
    - Example 1: For *uncompressed* files named using a format like `CH-FRU_ec_20230509-0930_withAGC.dat`, the
      respective entry is `ec_yyyymmdd-HHMM_withAGC.dat`. The site name `CH-FRU_` is added automatically during
      processing and must not be added in this setting.
    - Example 2: For *uncompressed* files named using a format like `CH-FRU_202305090930.csv`, the respective
      entry is `yyyymmddHHMM` (same as in earlier version). The site name `CH-FRU_` is added automatically during
      processing and must not be added in this setting. The file extension `.csv` is assumed since no specific file
      extension is given.
    - Example 3: For *compressed* files named using a format like `CH-FRU_ec_20230509-0930_withAGC.dat.gz`, the
      respective entry is `ec_yyyymmdd-HHMM_withAGC.dat`. The suffix `.gz` is automatically added to the given file
      extension.
    - Example 4: For *compressed* files named using a format like `CH-FRU_202305090930.csv.gz`, the respective
      entry is `yyyymmddHHMM` (same as in earlier version).
- Added: During unzipping of gzip files, the logger now also displays the name of the file before unzipping
  is started. This way it is easier to identify files for which unzipping does not work, e.g., due to
  corrupted binary files (irregular structure). (`fluxrun.ops.file.uncompress_gzip`)

## v1.3.2 | 21 Oct 2023

- Moved repo to GitLab: https://github.com/holukas/fluxrun

## v1.3.1 - 1 Jul 2023

- Updated poetry.lock file
- Updated version number, was wrong in last release, should have been v1.3.0 in toml

## v1.3.0 - 2 Apr 2023

- New setting in `Output` > `After Processing` > `Delete uncompressed raw data ASCII`:
  if selected, the uncompressed raw data files (ASCII) are deleted after finished flux
  calculations. The *compressed* raw data ASCII files are not affected by this setting.
  Background: for EddyPro flux calculations, the zipped files are uncompressed to regular
  ASCII files. These uncompressed files are not required for long-term storage because they
  take up a lot of disk space. For storage, we keep the zipped (compressed) ASCII files.

## v1.2.0 - 20 Mar 2023

- Now using `poetry` as dependency manager
- Removed `setup.py`, not needed with `poetry`
- Removed `environment.yml`, not needed with `poetry`
- Removed `start_fluxrun.py`, GUI is now started with CLI `-g` flag

## v1.1.1 - 18 Dec 2022

- Fixed bug where calculations from previously uncompressed `.csv.gz` files would not
  work. `fluxrun` tried to write an informal `readme.txt` to the output folder of the
  current run, but the folder did not yet exist. Output folders are now created before
  the EddyPro raw data folder is set in `fluxrun.FluxRunEngine.update_settings`.
    - `make_outdirs(settings_dict=self.settings_dict)` now comes first
    - `self.set_dir_eddypro_rawdata()` now comes second

## v1.1 - 4 Nov 2022

- Refactored code
- Functionality is now separated into `FluxRunGUI` for the graphical user interface,
  and `FluxRunEngine` for calculations. This is needed to execute the script without
  the GUI via CLI.
- Started to implement script execution via CLI: `-g` as arg starts the `fluxrun` GUI
- Added CLI args to start script without GUI
- Derived settings, .i.e., setttings that are constructed from parameters given
  in the GUI, are now reset when the app starts
- Updated all packages in conda env to latest compatible versions

## v1.0.4 - 8 Aug 2022

- updated EddyPro version to v7.0.9
- updated links in sidebar
- comboboxes are now minimum width 150px to avoid cutting off text elements

## v1.0.3 - 11 Dec 2021

- update: now using EddyPro v7.0.8

## v1.0.2 - 5 Oct 2021

- added `CH-DAS` to site selection

## v1.0.1 - 12 Aug 2021

- updated version number and dates in code

## v1.0 - 12 Aug 2021

- update: now using EddyPro v7.0.7
- update: new, slimmer conda environment `FLUXRUN` with updated pandas,  
  numpy, matplotlib and pyqt
- code: plots are now explicitely closed after saving to avoid the  
  "More than 20 figures have been opened." warning in matplotlib
- added: info about used EddyPro version in sidebar

## v0.5.0 - 16 Mar 2021

- bug: removed bug where another .metadata file, found in a subfolder in the
  .eddypro file folder, would be used (os.walk took it too far)

## v0.4.0 - 23 Feb 2021

- changed: plots now generated strictly from *uncompressed* raw data files
- updated: new, slimmer conda environment `FLUXRUN`
- changed: structure of .settings file

## v0.3.0 - 21 Feb 2021

- new: added option to plot aggregated raw data files. The plots show the
  data that is then used for flux calculations.
- changed: folder structure is now sequential to produced output
- changed: if 'ASCII File Compression' is set to 'None', then the raw data  
  files will be directly used from the provided source folder, i.e. in this  
  case the raw data files are not copied to the local run folder
- GUI: changed location of 'ASCII File Compression'

## v0.2.0 - 17 Feb 2021

- new: dedicated class for plotting EddyPro full_output files, adjusted code
- new: dedicated class for reading EddyPro full_output files

## v0.1.1 - 16 Feb 2021

- removed: unnecessary print statement

## v0.1.0 - 16 Feb 2021

- added: working links to left sidebar

## v0.0.1 - 13 Feb 2021

- initial commit

