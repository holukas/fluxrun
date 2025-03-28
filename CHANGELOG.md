# Changelog

![](images/logo_FLUXRUN1_256px.png)

## v1.5.0 | XX Jan 2025

- Now using PyQt6 for GUI
- Updated code for PyQt6
- Fixed bug in pandas `.pivot()` method, small issue due to the updated pandas version
- `diive` is now using Python version `3.11` upwards
- Updated environment, poetry `pyproject.toml` file now has the currently used structure
- Added key shortcut to start ("Ctrl+R")

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

