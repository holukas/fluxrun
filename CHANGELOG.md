# Changelog

![](images/logo_FLUXRUN1_256px.png)

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

