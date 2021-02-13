import datetime as dt
import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import dates
from matplotlib.ticker import MultipleLocator

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 15)
pd.set_option('display.max_rows', 20)


def plot_full_output(file_to_plot, destination_folder, logger):
    section_id = "[SUMMARY PLOTS]"

    # small function to read date column properly
    parse = lambda x: dt.datetime.strptime(x, '%Y-%m-%d %H:%M')  # standard date format of the EddyPro full_output file

    # read data file, generates data frame (similar to R)
    contents = pd.read_csv(file_to_plot, skiprows=[0, 2],
                           parse_dates=[['date', 'time']], index_col=0, date_parser=parse)
    # read start of data file to get units (in 3rd row)

    # more info: http: // pandas.pydata.org / pandas - docs / stable / io.html  # duplicate-names-parsing
    units = pd.read_csv(file_to_plot, skiprows=[0, 1], nrows=1, mangle_dupe_cols=True)
    units = units.columns[2:]
    logger.info(units)

    # look at what date range of 30min data we have
    first_date = contents.index[0]  # first entry
    last_date = contents.index[-1]  # last entry
    logger.info("found first date: " + str(first_date))

    if last_date.day - first_date.day < 5:  # if we have less than 5 days of data add dates to avoid problems with results plotting
        last_date = last_date + pd.offsets.Day(20)
        logger.info("found last date (extended by 20 days for plotting): " + str(last_date))
    else:
        logger.info("found last date: " + str(last_date))

    # generate continuous date range and re-index data
    filled_date_range = pd.date_range(first_date, last_date, freq='30T')
    contents = contents.reindex(filled_date_range, fill_value=-9999)  # apply new continuous index to data

    plot_folder = os.path.join(destination_folder)

    # read columns names from file, count columns in file
    columns_names = contents.columns
    logger.info(columns_names)
    columns_count = len(contents.columns)
    logger.info("number of columns: " + str(columns_count))

    # assemble PNG output
    for scalar in range(2, columns_count):

        logger.info("working on: " + columns_names[scalar] + " (column #" + str(scalar) + " of " + str(columns_count) + ")")
        plot_name = str(scalar) + "_" + columns_names[scalar]

        plot_name = plot_name.replace('*', 'star')
        plot_name = plot_name.replace('/', '_over_')

        y = contents[columns_names[scalar]]

        # if qc flag available, filter for quality 0 and 1 fluxes, do not use quality 2 fluxes
        qc_string = "qc_" + columns_names[scalar]

        quality_controlled = 0  # 0 = no, 1 = yes
        if qc_string in columns_names:
            qc = contents[qc_string] < 2  # qc = quality control flags, 0 = very good, 1 = OK
            y = y[qc]
            quality_controlled = 1

        fig = plt.figure(figsize=(11.69, 6.58), dpi=300)

        y = y.replace('Infinity', np.nan)  # replace 'Infinity' string (if found...)
        y = y.replace('-Infinity', np.nan)  # replace '-Infinity' string (if found...)
        y = y.replace('NaN', np.nan)  # should not be necessary... but is necessary sometimes!
        y = y.replace('#N/A', np.nan)  # should not be necessary...
        y = y.replace('#NV', np.nan)  # should not be necessary...
        y = y.astype(float)  # convert Series to NUMERIC
        y = y.replace(-9999, np.nan)  # general missing value
        y = y.replace(-6999, np.nan)  # special missing value used for some scalars, e.g. ch4
        y = y.dropna()  # remove all missing values
        # unique_values = np.unique(y)

        if not y.empty:  # and len(unique_values) > 1:

            heading_size = 8
            label_size = 7
            text_size = 8

            # fig = plt.subplot2grid((3, 3), (0, 0))

            qua1 = y.quantile(0.01)
            qua2 = y.quantile(0.99)

            # TIME SERIES PLOT
            ax1 = plt.subplot2grid((4, 4), (0, 0), colspan=4, rowspan=2)
            # y.plot(kind='scatter', x=y.index, y=y, ax=ax1)
            # y.plot(c='#5f87ae', linewidth=0.3)  # green=#bdd442
            # plt.scatter(y.index, y, c='#5f87ae', edgecolor='#5f87ae', alpha=1, s=1)
            # ax1.plot_date(y.index.to_pydatetime(), y, 'o-', color='#5f87ae', linewidth=0.2, markersize=3, markeredgecolor='#5f87ae')  # http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.plot_date
            ax1.plot_date(y.index.to_pydatetime(), y, '-', color='#5f87ae',
                          linewidth=0.3)  # http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.plot_date
            plt.axhline(y.quantile(0.05), color='red', alpha=0.25)
            plt.axhline(y.quantile(0.95), color='red', alpha=0.25)
            ax1.set_xlabel("DAY/MONTH", size=label_size)
            ax1.set_ylabel(units[scalar], size=label_size)
            ax1.set_title(str(columns_names[scalar]) + " time series with 5/95 percentiles", size=heading_size,
                          backgroundcolor='#5f87ae')
            ax1.tick_params(axis='both', labelsize=label_size)
            # plt.setp(ax1.xaxis.get_majorticklabels(), rotation=0)
            ax1.xaxis.set_major_formatter(dates.DateFormatter("%d/%m"))
            # ax1.xaxis.set_major_locator(dates.WeekdayLocator(byweekday=1, interval=1))
            plt.ylim(qua1, qua2)

            # DAILY AVG SCATTER
            ax4 = plt.subplot2grid((4, 4), (2, 0), colspan=2)
            daily_count = y.resample('D').count()
            daily_avg = y.resample('D').mean()
            daily_std = y.resample('D').std()
            # daily_avg = daily_avg[daily_count > 10]
            # daily_std = daily_std[daily_count > 10]
            plt.scatter(daily_avg.index.to_pydatetime(), daily_avg, c='#f78b31', edgecolor='#f78b31', alpha=1, s=4)
            plt.errorbar(daily_avg.index.to_pydatetime(), daily_avg, alpha=0.2, yerr=daily_std, capsize=0, ls='none',
                         color='#f78b31', elinewidth=2)
            # plt.fill_between(daily_std.index, daily_avg - daily_std, daily_avg + daily_std, color='k', alpha=0.1)
            plt.axhline(0, color='grey', alpha=0.5)
            ax4.set_xlabel("DAY/MONTH", size=label_size)
            ax4.set_ylabel(units[scalar], size=label_size)
            ax4.set_title(str(columns_names[scalar]) + " daily average with std", size=heading_size,
                          backgroundcolor='#f78b31')
            ax4.tick_params(axis='both', labelsize=label_size)
            plt.setp(ax4.xaxis.get_majorticklabels(), rotation=0)
            ax4.xaxis.set_major_formatter(dates.DateFormatter("%d/%m"))
            plt.ylim(qua1, qua2)
            # plt.ylim(-10, 10)

            # HISTOGRAM
            try:
                ax2 = plt.subplot2grid((4, 4), (3, 0), colspan=2)
                # y.hist(color='#5b9bd5', bins=10)
                # y_hist = y[y > qua1]
                plt.hist(y, bins=10, range=(qua1, qua2), color='#5b9bd5', edgecolor='#497CDD')
                # plt.xlim(qua1, qua2)
                ax2.set_xlabel(units[scalar], size=label_size)
                ax2.set_ylabel("counts", size=label_size)
                ax2.set_title(str(columns_names[scalar]) + " histogram", size=heading_size, backgroundcolor='#5b9bd5')
                ax2.tick_params(axis='both', labelsize=label_size)
            except ValueError as e:
                logger.info("(!)Error during histogram generation: {}".format(e))
                pass

            # CUMULATIVE
            ax5 = plt.subplot2grid((4, 4), (2, 2), colspan=2)
            # y.cumsum().plot(c='#ed3744', linewidth=0.6)
            ax5.plot_date(y.index.to_pydatetime(), y.cumsum(), '-', color='#ed3744', linewidth=0.6)
            ax5.set_xlabel("day/month", size=label_size)
            ax5.set_ylabel(units[scalar], size=label_size)
            ax5.set_title(str(columns_names[scalar]) + " cumulative", size=heading_size, backgroundcolor='#ed3744')
            ax5.tick_params(axis='both', labelsize=label_size)
            plt.setp(ax5.xaxis.get_majorticklabels(), rotation=0)
            ax5.xaxis.set_major_formatter(dates.DateFormatter("%d/%m"))
            # ax5.xaxis.set_major_locator(dates.MonthLocator())
            ax5.yaxis.grid()
            plt.axhline(0, color='black', alpha=0.8)

            # HOURLY AVERAGE
            ax6 = plt.subplot2grid((4, 4), (3, 2), colspan=1, rowspan=1)
            hourly_avg = y.groupby(y.index.hour).mean()
            hourly_std = y.groupby(y.index.hour).std()
            hourly_avg.plot()
            plt.fill_between(hourly_avg.index, hourly_avg - hourly_std, hourly_avg + hourly_std, color='k', alpha=0.1)
            ax6.set_xlabel("hour", size=label_size)
            ax6.set_ylabel(units[scalar], size=label_size)
            ax6.set_title(str(columns_names[scalar]) + " diurnal cycle with std", size=heading_size,
                          backgroundcolor='#ffc532')
            ax6.tick_params(axis='both', labelsize=label_size)
            plt.setp(ax6.xaxis.get_majorticklabels(), rotation=0)
            plt.axhline(0, color='black', alpha=0.8)
            plt.xlim(0, 23)
            if hourly_avg.min() < 0:
                factor = 1.2
            else:
                factor = 0.8
            plt.ylim(hourly_avg.min() * factor, hourly_avg.max() * 1.2)
            majorLocator = MultipleLocator(2)
            ax6.xaxis.set_major_locator(majorLocator)

            # TEXT INFO OUTPUT
            info_dict = y.describe().to_dict()
            info_txt = "\nSTATS\n"
            for key, val in info_dict.items():
                cur_info = f"{key}: {val}\n"
                info_txt += cur_info

            fig.text(0.8, 0.05, info_txt, size=text_size, backgroundcolor='#CCCCCC')
            if quality_controlled == 1:
                plt.figtext(0.84, 0.97, "quality controlled using " + qc_string, color='red', size=text_size)

            # plt.show()
            plt.tight_layout()
            # fig.subplots_adjust(hspace=0.1)
            logger.info("Saving plots to PNG image...")
            plot_name = os.path.join(plot_folder, plot_name)
            plt.savefig(plot_name + '.png', dpi=150)
            plt.close()

        else:
            logger.info("Data for " + columns_names[scalar] + " are empty --> no plot")

    logger.info("Finished full_output plots!")


# class PlotSummary:
#     section_txt = "[SUMMARY PLOTS]"
#
#     def __init__(self, file, destination_folder, logger):
#         self.file = file
#         self.destination_folder = destination_folder
#         self.logger = logger
#
#         # self.data_df, self.units, self.num_cols, self.colnames = self.prepare_plot_df()
#         self.data_df = self.read_full_output_file(filepath=file)
#
#     def run(self):
#         for ix, col in enumerate(self.data_df.columns):
#             self.info(ix=ix, col=col)
#             y, isnumeric, isempty = self.get_var_data(col=col)
#             if isempty or not isnumeric:
#                 continue
#             var_plotname = self.get_var_plotname(col=col)
#
#             self.make_axes()
#             self.timeseries_plot(ax=self.ax_timeseries, y=y)
#             self.heatmap(series=y, ax=self.ax_heatmap)
#
#             self.save_fig(var_plotname=var_plotname)
#
#     def save_fig(self, var_plotname):
#         print("Saving plots to PNG image...")
#         outfile = os.path.join(self.destination_folder, var_plotname)
#         plt.savefig(outfile + '.png', dpi=300)
#         plt.close()
#
#
#
#     def heatmap(self, series: pd.Series, ax):
#         import seaborn as sns
#
#         x_col = 'x_hour'
#         y_col = 'y_date'
#         z_col = 'z_vals'
#
#         heatmap_df = pd.DataFrame(index=series.index, columns=[x_col, y_col, z_col])
#         heatmap_df[z_col] = series.values
#         heatmap_df[x_col] = series.index.time
#         heatmap_df[y_col] = series.index.date
#
#         # heatmap plot
#         if heatmap_df[z_col].min() < 0 and heatmap_df[z_col].max() > 0:
#             # diverging
#             cmap = plt.get_cmap('RdYlBu')  # set colormap, see https://matplotlib.org/users/colormaps.html
#         else:
#             # sequential
#             cmap = plt.get_cmap('GnBu')
#
#         vmin = heatmap_df[z_col].quantile(0.01)
#         vmax = heatmap_df[z_col].quantile(0.99)
#
#         heatmap_df = heatmap_df[[x_col, y_col, z_col]]
#         heatmap_df = heatmap_df.pivot(index=y_col, columns=x_col, values=z_col)
#         heatmap_df.sort_index(ascending=False, inplace=True)
#
#         sns.heatmap(heatmap_df, cmap=cmap, vmin=vmin, vmax=vmax, center=0, ax=ax,
#                     square=False, linewidths=0, cbar_kws={"shrink": .5, "orientation": "horizontal"})
#
#         # self.default_format(ax=ax, txt_xlabel='Time',
#         #                     txt_ylabel='Date',
#         #                     txt_ylabel_units="L")
#         # self.nice_date_ticks(ax=ax, minticks=3, maxticks=40, which='x')
#
#         locator = mdates.AutoDateLocator(minticks=1, maxticks=52)
#         formatter = mdates.ConciseDateFormatter(locator, show_offset=False)
#         ax.yaxis.set_major_locator(locator)
#         ax.yaxis.set_major_formatter(formatter)
#
#         # ax.yaxis.set_major_locator(locator)
#         # ax.yaxis.set_major_formatter(formatter)
#         return None
#
#
#     def make_axes(self):
#         # Setup grid for multiple axes
#         self.fig = plt.figure(figsize=(11.69, 6.58), dpi=300)
#         gs = gridspec.GridSpec(2, 10)  # rows, cols
#         gs.update(wspace=0.3, hspace=0.3, left=0.08, right=0.97, top=0.96, bottom=0.05)
#
#         self.ax_timeseries = self.fig.add_subplot(gs[0:1, 0:8])
#         self.ax_heatmap = self.fig.add_subplot(gs[0:2, 8:10])
#         # self.ax2_cumsum = self.fig.add_subplot(gs[2:3, 0:1])
#         # self.ax7_daily_avg = self.fig.add_subplot(gs[2:3, 1:2])
#         # self.ax8_rainbow_diel_cycle_avg = self.fig.add_subplot(gs[2:3, 2:3])
#         # self.ax3_histogram = self.fig.add_subplot(gs[2:3, 3:4])
#         return gs
#
#     def info(self, ix, col):
#         self.logger.info(f"{self.section_txt} "
#                          f"#{ix} of {len(self.data_df.columns)}:  VAR {col[0]}    UNITS {col[1]}    "
#                          f"(column #{ix} of {len(self.data_df.columns)})")
#
#     def get_var_plotname(self, col):
#         var_plotname = f"{col[0]}_{col[1]}"
#         var_plotname = var_plotname.replace('*', 'star')
#         var_plotname = var_plotname.replace('/', '_over_')
#         return var_plotname
#
#     def get_var_data(self, col):
#         y = self.data_df[col]
#
#         # # if qc flag available, filter for quality 0 and 1 fluxes, do not use quality 2 fluxes
#         # qc_string = "qc_" + self.colnames[col]
#         # quality_controlled = False
#         # if qc_string in self.colnames:
#         #     qc = self.data_df[qc_string] < 2  # qc = quality control flags, 0 = very good, 1 = OK
#         #     y = y[qc]
#         #     quality_controlled = True
#
#         y = y.replace('Infinity', np.nan)  # replace 'Infinity' string (if found...)
#         y = y.replace('-Infinity', np.nan)  # replace '-Infinity' string (if found...)
#         y = y.replace('NaN', np.nan)  # should not be necessary... but is necessary sometimes!
#         y = y.replace('#N/A', np.nan)  # should not be necessary...
#         y = y.replace('#NV', np.nan)  # should not be necessary...
#         y = y.replace(-9999, np.nan)  # general missing value
#         y = y.replace(-6999, np.nan)  # special missing value used for some scalars, e.g. ch4
#
#         try:
#             y = y.astype(float)  # convert Series to NUMERIC
#             isnumeric = True
#         except ValueError:
#             self.logger.info(f"(!)WARNING Variable {y.name} is non-numeric and will be skipped (no plots).")
#             isnumeric = False
#
#         isempty = True if y.empty else False
#         if isempty:
#             self.logger.info(f"(!)WARNING Variable {y.name} is empty and will be skipped (no plots).")
#
#         # y = y.dropna()  # remove all missing values
#         return y, isnumeric, isempty
#
#     def read_full_output_file(self, filepath):
#         """Read file into df"""
#         # Check data
#         # ----------
#         more_data_cols_than_header_cols, num_missing_header_cols, header_cols_list, generated_missing_header_cols_list = \
#             self.compare_len_header_vs_data(filepath=filepath,
#                                             skip_rows_list=[0],
#                                             header_rows_list=[0, 1])
#
#         # Read data file
#         # --------------
#         # Column settings for parsing dates / times correctly
#         parsed_index_col = ('index', '[parsed]')
#         parse_dates = [('date', '[yyyy-mm-dd]'), ('time', '[HH:MM]')]
#         parse_dates = {parsed_index_col: parse_dates}
#         date_parser = lambda x: dt.datetime.strptime(x, '%Y-%m-%d %H:%M')
#
#         data_df = pd.read_csv(filepath,
#                               skiprows=[0, 1, 2],  # Data header section rows
#                               header=None,
#                               names=header_cols_list,
#                               na_values=-9999,
#                               encoding='utf-8',
#                               delimiter=',',
#                               mangle_dupe_cols=True,
#                               keep_date_col=False,
#                               parse_dates=parse_dates,
#                               date_parser=date_parser,
#                               index_col=None,
#                               dtype=None,
#                               engine='python')
#
#         # There exist certain instances where the float64 data column can contain
#         # non-numeric values that are interpreted as a float64 inf, which is basically
#         # a NaN value. To harmonize missing values inf is also set to NaN.
#         data_df = data_df.replace(float('inf'), np.nan)
#         data_df = data_df.replace(float('-inf'), np.nan)
#
#         # Additional safeguards
#         data_df = data_df.replace(-6999, np.nan)  # Special missing value used for some scalars, e.g. ch4
#         data_df = data_df.replace('Infinity', np.nan)  # Replace 'Infinity' string (if found...)
#         data_df = data_df.replace('-Infinity', np.nan)
#
#         data_df = self.standardize_index(df=data_df)
#
#         return data_df
#
#     def standardize_index(self, df):
#         # Index name is now the same for all filetypes w/ timestamp in data
#         df.set_index([('index', '[parsed]')], inplace=True)
#         df.index.name = ('TIMESTAMP', '[yyyy-mm-dd HH:MM:SS]')
#         # Make sure the index is datetime
#         df.index = pd.to_datetime(df.index)
#         return df
#
#     def compare_len_header_vs_data(self, filepath, skip_rows_list, header_rows_list):
#         """
#         Check whether there are more data columns than given in the header.
#
#         If not checked, this would results in an error when reading the csv file
#         with .read_csv, because the method expects an equal number of header and
#         data columns. If this check is True, then the difference between the length
#         of the first data row and the length of the header row(s) can be used to
#         automatically generate names for the missing header columns.
#         """
#         # Check number of columns of the first data row after the header part
#         skip_num_lines = len(header_rows_list) + len(skip_rows_list)
#         first_data_row_df = pd.read_csv(filepath, skiprows=skip_num_lines,
#                                         header=None, nrows=1)
#         len_data_cols = first_data_row_df.columns.size
#
#         # Check number of columns of the header part
#         header_cols_df = pd.read_csv(filepath, skiprows=skip_rows_list,
#                                      header=header_rows_list, nrows=0)
#         len_header_cols = header_cols_df.columns.size
#
#         # Check if there are more data columns than header columns
#         if len_data_cols > len_header_cols:
#             more_data_cols_than_header_cols = True
#             num_missing_header_cols = len_data_cols - len_header_cols
#         else:
#             more_data_cols_than_header_cols = False
#             num_missing_header_cols = 0
#
#         # Generate missing header columns if necessary
#         header_cols_list = header_cols_df.columns.to_list()
#         generated_missing_header_cols_list = []
#         sfx = self.make_timestamp_microsec_suffix()
#         if more_data_cols_than_header_cols:
#             for m in list(range(1, num_missing_header_cols + 1)):
#                 missing_col = (f'unknown_{m}-{sfx}', '[-unknown-]')
#                 generated_missing_header_cols_list.append(missing_col)
#                 header_cols_list.append(missing_col)
#
#         return more_data_cols_than_header_cols, num_missing_header_cols, header_cols_list, generated_missing_header_cols_list
#
#     def make_timestamp_microsec_suffix(self):
#         now_time_dt = dt.datetime.now()
#         now_time_str = now_time_dt.strftime("%H%M%S%f")
#         run_id = f'{now_time_str}'
#         # log(name=make_run_id.__name__, dict={'run id': run_id}, highlight=False)
#         return run_id
#
#     def prepare_plot_df(self):  # todo
#         # Small function to read date column properly
#         parse = lambda x: dt.datetime.strptime(x,
#                                                '%Y-%m-%d %H:%M')  # standard date format of the EddyPro full_output file
#
#         # Read data file
#         self.logger.info(f"{self.section_txt} Reading EddyPro full_output file {self.file} ...")
#         data_df = pd.read_csv(self.file, skiprows=[0], header=[0, 1],
#                               parse_dates=[[('date', '[yyyy-mm-dd]'), ('time', '[HH:MM]')]],
#                               index_col=0, date_parser=parse)
#
#         # Read start of data file to get units (in 3rd row)
#         units = pd.read_csv(self.file, skiprows=[0, 1], nrows=1, mangle_dupe_cols=True)
#         units = units.columns[2:]
#         self.logger.info(f"{self.section_txt} {units}")
#
#         # Look at what date range of 30min data we have
#         first_date = data_df.index[0]  # first entry
#         last_date = data_df.index[-1]  # last entry
#         self.logger.info(f"{self.section_txt} Found first date in data: " + str(first_date))
#         if last_date.day - first_date.day < 5:  # if we have less than 5 days of data add dates to avoid problems with results plotting
#             last_date = last_date + pd.offsets.Day(20)
#             self.logger.info(
#                 f"{self.section_txt} Found last date in data (extended by 20 days for plotting): " + str(last_date))
#         else:
#             self.logger.info(f"{self.section_txt} Found last date in data: " + str(last_date))
#
#         # Generate continuous date range and re-index data
#         filled_date_range = pd.date_range(first_date, last_date, freq='30T')
#         data_df = data_df.reindex(filled_date_range, fill_value=-9999)  # apply new continuous index to data
#
#         # read columns names from file, count columns in file
#         colnames = data_df.columns
#         self.logger.info(f"{self.section_txt} Column names: {colnames}")
#         num_cols = len(data_df.columns)
#         self.logger.info(f"{self.section_txt} Number of columns: {num_cols}")
#
#         return data_df, units, num_cols, colnames
#
#     def format_spines(self, ax, color, lw):
#         spines = ['top', 'bottom', 'left', 'right']
#         for spine in spines:
#             ax.spines[spine].set_color(color)
#             ax.spines[spine].set_linewidth(lw)
#         return None
#
#     def default_format(self, ax, fontsize=10, label_color='black',
#                        txt_xlabel='', txt_ylabel='', txt_ylabel_units='',
#                        width=0.5, length=3, direction='in', colors='black', facecolor='white'):
#         """ Apply default format to plot. """
#         ax.set_facecolor(facecolor)
#         ax.tick_params(axis='x', width=width, length=length, direction=direction, colors=colors, labelsize=fontsize)
#         ax.tick_params(axis='y', width=width, length=length, direction=direction, colors=colors, labelsize=fontsize)
#         self.format_spines(ax=ax, color=colors, lw=1)
#         if txt_xlabel:
#             ax.set_xlabel(txt_xlabel, color=label_color, fontsize=fontsize, fontweight='bold')
#         if txt_ylabel and txt_ylabel_units:
#             ax.set_ylabel(f'{txt_ylabel}  {txt_ylabel_units}', color=label_color, fontsize=fontsize, fontweight='bold')
#         if txt_ylabel and not txt_ylabel_units:
#             ax.set_ylabel(f'{txt_ylabel}', color=label_color, fontsize=fontsize, fontweight='bold')
#         return None
#
#     def default_grid(self, ax):
#         ax.grid(True, ls='--', color='#CFD8DC', lw=1, zorder=0)
#
#     def timeseries_plot(self, ax, y):
#         """
#         Make line plot with dates for full timeseries.
#         """
#
#         ax.plot_date(x=y.index, y=y, alpha=1, ls='-',
#                      zorder=99, label=y.name,
#                      marker='o',
#                      color='#1565C0',
#                      lw=1,
#                      markeredgecolor='#1565C0',
#                      ms=3)
#
#         ax.text(0.02, 0.97, f"{y.name[0]}  {y.name[1]}",
#                 size=10, color='black', backgroundcolor='none', fontweight='bold',
#                 transform=ax.transAxes, alpha=0.9,
#                 horizontalalignment='left', verticalalignment='top')
#
#         ymin = y.min()
#         ymax = y.max()
#         ax.set_ylim(ymin, ymax)
#
#         if (ymin < 0) & (ymax > 0):
#             ax.axhline(y=0, color='black', ls='-', lw=1, alpha=1, zorder=100)
#
#         self.default_format(ax=ax, txt_xlabel='Date',
#                             txt_ylabel=y.name[0],
#                             txt_ylabel_units=y.name[1])
#
#         self.default_grid(ax=ax)
#         self.nice_date_ticks(ax=ax, minticks=3, maxticks=40, which='x')
#
#     def nice_date_ticks(self, ax, minticks, maxticks, which):
#         """ Nice format for date ticks. """
#         locator = mdates.AutoDateLocator(minticks=minticks, maxticks=maxticks)
#         formatter = mdates.ConciseDateFormatter(locator, show_offset=False)
#         if which == 'y':
#             ax.yaxis.set_major_locator(locator)
#             ax.yaxis.set_major_formatter(formatter)
#         elif which == 'x':
#             ax.xaxis.set_major_locator(locator)
#             ax.xaxis.set_major_formatter(formatter)
#         return None


# def plot_full_output(file: str, destination_folder, logger):
#     # assemble PNG output
#     # for scalar in range(2, num_cols):
#
#     # logger.info(f"{section_txt} Working on: {colnames[scalar]} (column #{scalar} of {num_cols})")
#     # plot_name = f"{scalar}_{colnames[scalar]}"
#     # plot_name = plot_name.replace('*', 'star')
#     # plot_name = plot_name.replace('/', '_over_')
#     #
#     # y = data_df[colnames[scalar]]
#     #
#     # # if qc flag available, filter for quality 0 and 1 fluxes, do not use quality 2 fluxes
#     # qc_string = "qc_" + colnames[scalar]
#     #
#     # quality_controlled = 0  # 0 = no, 1 = yes
#     # if qc_string in colnames:
#     #     qc = data_df[qc_string] < 2  # qc = quality control flags, 0 = very good, 1 = OK
#     #     y = y[qc]
#     #     quality_controlled = 1
#
#     # fig = plt.figure(figsize=(11.69, 6.58), dpi=300)
#
#     # y = y.replace('Infinity', np.nan)  # replace 'Infinity' string (if found...)
#     # y = y.replace('-Infinity', np.nan)  # replace '-Infinity' string (if found...)
#     # y = y.replace('NaN', np.nan)  # should not be necessary... but is necessary sometimes!
#     # y = y.replace('#N/A', np.nan)  # should not be necessary...
#     # y = y.replace('#NV', np.nan)  # should not be necessary...
#     # y = y.astype(float)  # convert Series to NUMERIC
#     # y = y.replace(-9999, np.nan)  # general missing value
#     # y = y.replace(-6999, np.nan)  # special missing value used for some scalars, e.g. ch4
#     # y = y.dropna()  # remove all missing values
#     # # unique_values = np.unique(y)
#
#     if not y.empty:  # and len(unique_values) > 1:
#
#         heading_size = 8
#         label_size = 7
#         text_size = 8
#
#         # fig = plt.subplot2grid((3, 3), (0, 0))
#
#         qua1 = y.quantile(0.01)
#         qua2 = y.quantile(0.99)
#
#         # TIME SERIES PLOT
#         ax1 = plt.subplot2grid((4, 4), (0, 0), colspan=4, rowspan=2)
#         # y.plot(kind='scatter', x=y.index, y=y, ax=ax1)
#         # y.plot(c='#5f87ae', linewidth=0.3)  # green=#bdd442
#         # plt.scatter(y.index, y, c='#5f87ae', edgecolor='#5f87ae', alpha=1, s=1)
#         # ax1.plot_date(y.index.to_pydatetime(), y, 'o-', color='#5f87ae', linewidth=0.2, markersize=3, markeredgecolor='#5f87ae')  # http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.plot_date
#         ax1.plot_date(y.index.to_pydatetime(), y, '-', color='#5f87ae',
#                       linewidth=0.3)  # http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.plot_date
#         plt.axhline(y.quantile(0.05), color='red', alpha=0.25)
#         plt.axhline(y.quantile(0.95), color='red', alpha=0.25)
#         ax1.set_xlabel("DAY/MONTH", size=label_size)
#         ax1.set_ylabel(units[scalar], size=label_size)
#         ax1.set_title(str(colnames[scalar]) + " time series with 5/95 percentiles", size=heading_size,
#                       backgroundcolor='#5f87ae')
#         ax1.tick_params(axis='both', labelsize=label_size)
#         # plt.setp(ax1.xaxis.get_majorticklabels(), rotation=0)
#         ax1.xaxis.set_major_formatter(dates.DateFormatter("%d/%m"))
#         # ax1.xaxis.set_major_locator(dates.WeekdayLocator(byweekday=1, interval=1))
#         plt.ylim(qua1, qua2)
#
#         # DAILY AVG SCATTER
#         ax4 = plt.subplot2grid((4, 4), (2, 0), colspan=2)
#         daily_count = y.resample('D', how='count')
#         daily_avg = y.resample('D', how='mean')
#         daily_std = y.resample('D', how='std')
#         # daily_avg = daily_avg[daily_count > 10]
#         # daily_std = daily_std[daily_count > 10]
#         plt.scatter(daily_avg.index.to_pydatetime(), daily_avg, c='#f78b31', edgecolor='#f78b31', alpha=1, s=4)
#         plt.errorbar(daily_avg.index.to_pydatetime(), daily_avg, alpha=0.2, yerr=daily_std, capsize=0, ls='none',
#                      color='#f78b31', elinewidth=2)
#         # plt.fill_between(daily_std.index, daily_avg - daily_std, daily_avg + daily_std, color='k', alpha=0.1)
#         plt.axhline(0, color='grey', alpha=0.5)
#         ax4.set_xlabel("DAY/MONTH", size=label_size)
#         ax4.set_ylabel(units[scalar], size=label_size)
#         ax4.set_title(str(colnames[scalar]) + " daily average with std", size=heading_size,
#                       backgroundcolor='#f78b31')
#         ax4.tick_params(axis='both', labelsize=label_size)
#         plt.setp(ax4.xaxis.get_majorticklabels(), rotation=0)
#         ax4.xaxis.set_major_formatter(dates.DateFormatter("%d/%m"))
#         plt.ylim(qua1, qua2)
#         # plt.ylim(-10, 10)
#
#         # HISTOGRAM
#         try:
#             ax2 = plt.subplot2grid((4, 4), (3, 0), colspan=2)
#             # y.hist(color='#5b9bd5', bins=10)
#             # y_hist = y[y > qua1]
#             plt.hist(y, bins=10, range=(qua1, qua2), color='#5b9bd5', edgecolor='#497CDD')
#             # plt.xlim(qua1, qua2)
#             ax2.set_xlabel(units[scalar], size=label_size)
#             ax2.set_ylabel("counts", size=label_size)
#             ax2.set_title(str(colnames[scalar]) + " histogram", size=heading_size, backgroundcolor='#5b9bd5')
#             ax2.tick_params(axis='both', labelsize=label_size)
#         except ValueError as e:
#             print("(!)Error during histogram generation: {}".format(e))
#             pass
#
#         # CUMULATIVE
#         ax5 = plt.subplot2grid((4, 4), (2, 2), colspan=2)
#         # y.cumsum().plot(c='#ed3744', linewidth=0.6)
#         ax5.plot_date(y.index.to_pydatetime(), y.cumsum(), '-', color='#ed3744', linewidth=0.6)
#         ax5.set_xlabel("day/month", size=label_size)
#         ax5.set_ylabel(units[scalar], size=label_size)
#         ax5.set_title(str(colnames[scalar]) + " cumulative", size=heading_size, backgroundcolor='#ed3744')
#         ax5.tick_params(axis='both', labelsize=label_size)
#         plt.setp(ax5.xaxis.get_majorticklabels(), rotation=0)
#         ax5.xaxis.set_major_formatter(dates.DateFormatter("%d/%m"))
#         # ax5.xaxis.set_major_locator(dates.MonthLocator())
#         ax5.yaxis.grid()
#         plt.axhline(0, color='black', alpha=0.8)
#
#         # # TIME SERIES MEDIAN PLOT w/ QUANTILES
#         #     ax3 = plt.subplot2grid((4, 4), (3, 0), colspan=2)
#         #     rmed = rolling_median(y, 50)  # rolling median value
#         #     # rmed.plot(style='k')
#         #     ax3.plot_date(rmed.index.to_pydatetime(), rmed, '-', color='#ed3744', linewidth=0.6)
#         #     rqua75 = rolling_quantile(y, 50, 0.75)  # rolling quantile
#         #     rqua25 = rolling_quantile(y, 50, 0.25)
#         #     plt.fill_between(rqua75.index, rqua25, rqua75, color='b', alpha=0.2)
#         #     ax3.set_xlabel("day/month", size=label_size)
#         #     ax3.set_ylabel(units[scalar], size=label_size)
#         #     ax3.set_title(str(columns_names[scalar]) + " running median (50 values) + running 25/75 percentile",
#         #                   size=heading_size, backgroundcolor='#6e8588')
#         #     ax3.tick_params(axis='both', labelsize=label_size)
#         #     # plt.setp(ax3.xaxis.get_majorticklabels(), rotation=0)
#         #     ax3.xaxis.set_major_formatter(dates.DateFormatter("%d/%m"))
#
#         # HOURLY AVERAGE
#         ax6 = plt.subplot2grid((4, 4), (3, 2), colspan=1, rowspan=1)
#         hourly_avg = y.groupby(y.index.hour).mean()
#         hourly_std = y.groupby(y.index.hour).std()
#         hourly_avg.plot()
#         plt.fill_between(hourly_avg.index, hourly_avg - hourly_std, hourly_avg + hourly_std, color='k', alpha=0.1)
#         ax6.set_xlabel("hour", size=label_size)
#         ax6.set_ylabel(units[scalar], size=label_size)
#         ax6.set_title(str(colnames[scalar]) + " diurnal cycle with std", size=heading_size,
#                       backgroundcolor='#ffc532')
#         ax6.tick_params(axis='both', labelsize=label_size)
#         plt.setp(ax6.xaxis.get_majorticklabels(), rotation=0)
#         plt.axhline(0, color='black', alpha=0.8)
#         plt.xlim(0, 23)
#         if hourly_avg.min() < 0:
#             factor = 1.2
#         else:
#             factor = 0.8
#         plt.ylim(hourly_avg.min() * factor, hourly_avg.max() * 1.2)
#         majorLocator = MultipleLocator(2)
#         ax6.xaxis.set_major_locator(majorLocator)
#
#         # TEXT INFO OUTPUT
#         fig.text(0.8, 0.05, y.describe(), size=text_size, backgroundcolor='#CCCCCC')
#         if quality_controlled == 1:
#             plt.figtext(0.84, 0.97, "quality controlled using " + qc_string, color='red', size=text_size)
#
#         # plt.show()
#         plt.tight_layout()
#         # fig.subplots_adjust(hspace=0.1)
#         print("Saving plots to PNG image...")
#         plot_name = os.path.join(destination_folder, plot_name)
#         plt.savefig(plot_name + '.png', dpi=150)
#         plt.close()
#
#     else:
#         print("Data for " + colnames[scalar] + " is empty --> no plot")


print("Finished full_output plots!")


def availability_rawdata(rawdata_found_files_dict, rawdata_file_datefrmt, outdir, logger):
    """
    Plot data availability from datetime info in filenames

    Kudos:
        https://matplotlib.org/3.2.2/gallery/images_contours_and_fields/image_annotated_heatmap.html
    """

    logger.info("Plotting availability heatmap ...")

    # Prepare data for plot
    plot_df = pd.DataFrame()
    for rawdata_file, rawdata_filepath in rawdata_found_files_dict.items():
        rawdata_filebin_filedate = dt.datetime.strptime(rawdata_filepath.name, rawdata_file_datefrmt)
        plot_df.loc[rawdata_filebin_filedate, 'date'] = rawdata_filebin_filedate.date()
        plot_df.loc[rawdata_filebin_filedate, 'filesize'] = os.path.getsize(rawdata_filepath) / 1000000  # in MB

    agg_plot_df = plot_df.groupby('date').agg('sum')
    agg_plot_df.index = pd.to_datetime(agg_plot_df.index)
    plot_range = pd.date_range(agg_plot_df.index[0], agg_plot_df.index[-1], freq='1D')
    agg_plot_df = agg_plot_df.reindex(plot_range)

    agg_plot_df['day'] = agg_plot_df.index.day
    agg_plot_df['month'] = agg_plot_df.index.month
    agg_plot_df['year'] = agg_plot_df.index.year
    agg_plot_df['year-month'] = agg_plot_df.index.strftime('%Y-%m')
    agg_plot_df = agg_plot_df.pivot("year-month", "day", "filesize")
    days = [str(xx) for xx in agg_plot_df.columns]
    months = [str(yy) for yy in agg_plot_df.index]

    # Figure
    # fig, axes = plt.subplots(figsize=(16, 9))
    # gs = gridspec.GridSpec(1, 1)  # rows, cols
    # gs.update(wspace=0.2, hspace=0.2, left=0.03, right=0.97, top=0.97, bottom=0.03)
    # ax = fig.add_subplot(gs[0, 0])
    fig, ax = plt.subplots(1, 1, figsize=(16, 9))
    ax.set_title("Filesizes of binary raw data per day")

    # Colormap
    cmap = plt.get_cmap('RdYlBu')
    agg_plot_df = np.ma.masked_invalid(agg_plot_df)  # Mask NaN as missing
    cmap.set_bad(color='#EEEEEE', alpha=1.)  # Set missing data to specific color

    # Data
    im = ax.imshow(agg_plot_df, cmap=cmap, aspect='equal', vmin=0)

    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax, format='%.0f')
    cbar.ax.set_ylabel('Filesize [MB]', rotation=-90, va="bottom")

    # We want to show all ticks...
    ax.set_xticks(np.arange(len(days)))
    ax.set_yticks(np.arange(len(months)))
    # ... and label them with the respective list entries
    ax.set_xticklabels(days)
    ax.set_yticklabels(months)

    # Turn spines off and create white grid.
    # for edge, spine in ax.spines.items():
    #     spine.set_visible(False)
    ax.set_xticks(np.arange(agg_plot_df.shape[1] + 1) - .5, minor=True)
    ax.set_yticks(np.arange(agg_plot_df.shape[0] + 1) - .5, minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=1)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Save
    out_file = outdir / f"file_availability_heatmap"
    plt.savefig(f"{out_file}.png", dpi=150, bbox_inches='tight')
    plt.close()

    return None


def _format_spines(ax, color, lw):
    spines = ['top', 'bottom', 'left', 'right']
    for spine in spines:
        ax.spines[spine].set_color(color)
        ax.spines[spine].set_linewidth(lw)


def _default_format(ax, fontsize=12, label_color='black',
                    txt_xlabel='', txt_ylabel='', txt_ylabel_units='',
                    width=1, length=5, direction='in', colors='black', facecolor='white'):
    """Apply default format to plot."""
    ax.set_facecolor(facecolor)
    ax.tick_params(axis='x', width=width, length=length, direction=direction, colors=colors, labelsize=fontsize,
                   top=True)
    ax.tick_params(axis='y', width=width, length=length, direction=direction, colors=colors, labelsize=fontsize,
                   right=True)
    _format_spines(ax=ax, color=colors, lw=0.5)
    if txt_xlabel:
        ax.set_xlabel(txt_xlabel, color=label_color, fontsize=fontsize, fontweight='bold')
    if txt_ylabel and txt_ylabel_units:
        ax.set_ylabel(f'{txt_ylabel}  {txt_ylabel_units}', color=label_color, fontsize=fontsize, fontweight='bold')
    if txt_ylabel and not txt_ylabel_units:
        ax.set_ylabel(f'{txt_ylabel}', color=label_color, fontsize=fontsize, fontweight='bold')


def _format_plot(self, ax, title, show_legend=True):
    # Automatic tick locations and formats
    locator = mdates.AutoDateLocator(minticks=5, maxticks=20)
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    _default_format(ax=ax, label_color='black', fontsize=12,
                    txt_xlabel='file date', txt_ylabel='covariance', txt_ylabel_units='')

    font = {'family': 'sans-serif', 'color': 'black', 'weight': 'bold', 'size': 12, 'alpha': 1}
    ax.set_title(title, fontdict=font, loc='left', pad=12)

    ax.axhline(0, color='black', ls='-', lw=1, zorder=1)
    font = {'family': 'sans-serif', 'size': 10}
    if show_legend:
        ax.legend(frameon=True, loc='upper right', prop=font).set_zorder(100)
