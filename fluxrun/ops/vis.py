import datetime as dt
import os

import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import dates
from matplotlib.ticker import MultipleLocator

from ops.file import ReadEddyProFullOutputFile

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 15)
pd.set_option('display.max_rows', 20)


def sanitize_y(y):
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
    return y


class PlotEddyProFullOutputFile:
    section_id = "[SUMMARY PLOTS]"

    def __init__(self, file_to_plot, destination_folder, logger):
        self.file_to_plot = file_to_plot
        self.destination_folder = destination_folder
        self.logger = logger

        self.plot_folder = os.path.join(self.destination_folder)
        self.data_df = pd.DataFrame()

    def run(self):
        self.data_df = ReadEddyProFullOutputFile(filepath=self.file_to_plot).get()
        self.data_df = self.sanitize_daterange(df=self.data_df.copy())
        columns_names, columns_count = self.col_info()
        self.plot_full_output(columns_count, columns_names)

    def sanitize_daterange(self, df):
        # look at what date range of 30min data we have
        first_date = df.index[0]  # first entry
        last_date = df.index[-1]  # last entry
        self.logger.info("found first date: " + str(first_date))
        if last_date.day - first_date.day < 5:  # if we have less than 5 days of data add dates to avoid problems with results plotting
            last_date = last_date + pd.offsets.Day(20)
            self.logger.info("found last date (extended by 20 days for plotting): " + str(last_date))
        else:
            self.logger.info("found last date: " + str(last_date))
        # generate continuous date range and re-index data
        filled_date_range = pd.date_range(first_date, last_date, freq='30T')
        df = df.reindex(filled_date_range, fill_value=-9999)  # apply new continuous index to data
        return df

    def col_info(self):
        # read columns names from file, count columns in file
        columns_names = self.data_df.columns
        self.logger.info(columns_names)
        columns_count = len(self.data_df.columns)
        self.logger.info("number of columns: " + str(columns_count))
        return columns_names, columns_count

    def plot_full_output(self, columns_count, columns_names):
        """Assemble PNG output"""

        for ix, col in enumerate(self.data_df.columns):

            fig = plt.figure(figsize=(11.69, 6.58), dpi=300)
            var = col[0]
            units = col[1]

            self.logger.info(f"Working on: {col} (column #{ix} of {columns_count}) ...")
            plot_name = f"{ix}_{var}_{units}"
            plot_name = plot_name.replace('*', 'star')
            plot_name = plot_name.replace('/', '_over_')

            try:
                y = self.data_df[col].astype(float)
            except ValueError:
                self.logger.info(f"(!)WARNING: Skipping plotting for {col} because it is not numeric.")
                continue

            y = sanitize_y(y=y)

            # if qc flag available, filter for quality 0 and 1 fluxes, do not use quality 2 fluxes
            qc_col = (f"qc_{var}", '[#]')
            quality_controlled = 0  # 0 = no, 1 = yes
            if qc_col in columns_names:
                qc = self.data_df[qc_col] < 2  # qc = quality control flags, 0 = very good, 1 = OK
                y = y[qc]
                quality_controlled = 1

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
                ax1.axhline(y.quantile(0.05), color='red', alpha=0.25)
                ax1.axhline(y.quantile(0.95), color='red', alpha=0.25)
                ax1.set_xlabel("DAY/MONTH", size=label_size)
                ax1.set_ylabel(units, size=label_size)
                ax1.set_title(f"{var} time series with 5/95 percentiles", size=heading_size,
                              backgroundcolor='#5f87ae')
                ax1.tick_params(axis='both', labelsize=label_size)
                # plt.setp(ax1.xaxis.get_majorticklabels(), rotation=0)
                ax1.xaxis.set_major_formatter(dates.DateFormatter("%d/%m"))
                # ax1.xaxis.set_major_locator(dates.WeekdayLocator(byweekday=1, interval=1))
                ax1.set_ylim(qua1, qua2)

                # DAILY AVG SCATTER
                ax4 = plt.subplot2grid((4, 4), (2, 0), colspan=2)
                daily_count = y.resample('D').count()
                daily_avg = y.resample('D').mean()
                daily_std = y.resample('D').std()
                # daily_avg = daily_avg[daily_count > 10]
                # daily_std = daily_std[daily_count > 10]
                ax4.scatter(daily_avg.index.to_pydatetime(), daily_avg, c='#f78b31', edgecolor='#f78b31', alpha=1, s=4)
                ax4.errorbar(daily_avg.index.to_pydatetime(), daily_avg, alpha=0.2, yerr=daily_std, capsize=0,
                             ls='none',
                             color='#f78b31', elinewidth=2)
                # plt.fill_between(daily_std.index, daily_avg - daily_std, daily_avg + daily_std, color='k', alpha=0.1)
                ax4.axhline(0, color='grey', alpha=0.5)
                ax4.set_xlabel("DAY/MONTH", size=label_size)
                ax4.set_ylabel(units, size=label_size)
                ax4.set_title(f"{var} daily average with std", size=heading_size,
                              backgroundcolor='#f78b31')
                ax4.tick_params(axis='both', labelsize=label_size)
                plt.setp(ax4.xaxis.get_majorticklabels(), rotation=0)
                ax4.xaxis.set_major_formatter(dates.DateFormatter("%d/%m"))
                ax4.set_ylim(qua1, qua2)
                # plt.ylim(-10, 10)

                # HISTOGRAM
                try:
                    ax2 = plt.subplot2grid((4, 4), (3, 0), colspan=2)
                    # y.hist(color='#5b9bd5', bins=10)
                    # y_hist = y[y > qua1]
                    ax2.hist(y, bins=10, range=(qua1, qua2), color='#5b9bd5', edgecolor='#497CDD')
                    # plt.xlim(qua1, qua2)
                    ax2.set_xlabel(units, size=label_size)
                    ax2.set_ylabel("counts", size=label_size)
                    ax2.set_title(f"{var} histogram", size=heading_size, backgroundcolor='#5b9bd5')
                    ax2.tick_params(axis='both', labelsize=label_size)
                except ValueError as e:
                    self.logger.info("(!)Error during histogram generation: {}".format(e))
                    pass

                # CUMULATIVE
                ax5 = plt.subplot2grid((4, 4), (2, 2), colspan=2)
                # y.cumsum().plot(c='#ed3744', linewidth=0.6)
                ax5.plot_date(y.index.to_pydatetime(), y.cumsum(), '-', color='#ed3744', linewidth=0.6)
                ax5.set_xlabel("day/month", size=label_size)
                ax5.set_ylabel(units, size=label_size)
                ax5.set_title(f"{var} cumulative", size=heading_size, backgroundcolor='#ed3744')
                ax5.tick_params(axis='both', labelsize=label_size)
                plt.setp(ax5.xaxis.get_majorticklabels(), rotation=0)
                ax5.xaxis.set_major_formatter(dates.DateFormatter("%d/%m"))
                # ax5.xaxis.set_major_locator(dates.MonthLocator())
                ax5.yaxis.grid()
                ax5.axhline(0, color='black', alpha=0.8)

                # HOURLY AVERAGE
                ax6 = plt.subplot2grid((4, 4), (3, 2), colspan=1, rowspan=1)
                hourly_avg = y.groupby(y.index.hour).mean()
                hourly_std = y.groupby(y.index.hour).std()
                ax6.plot(hourly_avg)
                ax6.fill_between(hourly_avg.index, hourly_avg - hourly_std, hourly_avg + hourly_std, color='k',
                                 alpha=0.1)
                # hourly_avg.plot()
                # plt.fill_between(hourly_avg.index, hourly_avg - hourly_std, hourly_avg + hourly_std, color='k',
                #                  alpha=0.1)
                ax6.set_xlabel("hour", size=label_size)
                ax6.set_ylabel(units, size=label_size)
                ax6.set_title(f"{var} diurnal cycle with std", size=heading_size,
                              backgroundcolor='#ffc532')
                ax6.tick_params(axis='both', labelsize=label_size)
                plt.setp(ax6.xaxis.get_majorticklabels(), rotation=0)
                ax6.axhline(0, color='black', alpha=0.8)
                ax6.set_xlim(0, 23)
                if hourly_avg.min() < 0:
                    factor = 1.2
                else:
                    factor = 0.8
                ax6.set_ylim(hourly_avg.min() * factor, hourly_avg.max() * 1.2)
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
                    plt.figtext(0.84, 0.97, f"quality controlled using {qc_col}", color='red', size=text_size)

                plt.tight_layout()
                plot_name = os.path.join(self.plot_folder, plot_name)
                self.logger.info(f"    --> Saving plot {plot_name} ...")
                plt.savefig(plot_name + '.png', dpi=150)
                plt.close(fig)

            else:
                self.logger.info(f"Data for {col} are empty --> no plot")

        self.logger.info("Finished full_output plots!")


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
    agg_plot_df = agg_plot_df.pivot(index="year-month", columns="day", values="filesize")
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


class PlotRawDataFilesAggregates:
    section_id = "[PLOT RAW DATA FILE AGGREGATES]"

    def __init__(self, rawdata_found_files_dict, settings_dict, logger, rawdata_file_datefrmt):
        self.rawdata_found_files_dict = rawdata_found_files_dict
        self.settings_dict = settings_dict
        self.logger = logger
        self.rawdata_file_datefrmt = rawdata_file_datefrmt

        self.collect_aggs()

    def collect_aggs(self):
        """Loop"""
        filecounter = 0
        stats_coll_df = pd.DataFrame()
        num_files = len(self.rawdata_found_files_dict)
        for fid, filepath in self.rawdata_found_files_dict.items():
            filecounter += 1
            self.file_header_for_log(fid=fid, num_files=num_files, filecounter=filecounter)
            rawdata_filedate = self.get_filedate(fid)
            rawdata_df = self.read_uncompr_ascii_file(filepath=filepath)
            stats_coll_df = self.calc_rawdata_stats(rawdata_df=rawdata_df,
                                                    rawdata_filedate=rawdata_filedate,
                                                    stats_coll_df=stats_coll_df,
                                                    filecounter=filecounter)
        self.make_plot(df=stats_coll_df,
                       outdir=self.settings_dict['_dir_out_run_plots_aggregates_rawdata'])
        # print(filecounter)

    def file_header_for_log(self, fid, num_files, filecounter):
        spacer = "=" * 30
        self.logger.info(f"{self.section_id} {spacer}")
        self.logger.info(f"{self.section_id} File {fid} (#{filecounter} of {num_files}) ...")
        self.logger.info(f"{self.section_id} {spacer}")

    def read_uncompr_ascii_file(self, filepath):
        self.logger.info(f"{self.section_id}    Reading file {filepath} ...")
        import time
        tic = time.time()
        rawdata_df = pd.read_csv(filepath,
                                 skiprows=None,
                                 header=[0, 1, 2],
                                 na_values=-9999,
                                 encoding='utf-8',
                                 delimiter=',',
                                 # keep_date_col=True,
                                 parse_dates=False,
                                 # date_parser=None,
                                 index_col=None,
                                 dtype=None)
        time_needed = time.time() - tic
        self.logger.info(f"{self.section_id}    Finished ({time_needed:.3f}s). "
                         f"Detected {len(rawdata_df)} rows and {rawdata_df.columns.size} columns.")
        return rawdata_df

    def calc_rawdata_stats(self, rawdata_df, stats_coll_df, rawdata_filedate, filecounter):
        """Calculate stats for raw data"""
        self.logger.info(f"{self.section_id}    Calculating file stats ...")

        if rawdata_df.empty:
            # In case there are no data, create df with one row of NaNs
            rawdata_df = pd.DataFrame(index=[0], columns=rawdata_df.columns)

        # Replace missing values -9999 with NaNs for correct stats calcs
        rawdata_df.replace(-9999, np.nan, inplace=True)

        rawdata_df['index'] = rawdata_filedate
        rawdata_df.sort_index(axis=1, inplace=True)  # lexsort for better performance
        aggs = ['count', 'min', 'max', 'mean', 'std', 'median', self.q01, self.q05, self.q95, self.q99]
        rawdata_df = rawdata_df.groupby('index').agg(aggs)

        # else:
        #     # In case there are no data in the file, create a dataframe containing only missing
        #     # values and add it to the stats collection.
        #     else:
        #         num_cols = stats_coll_df.columns.size  # Count number of columns
        #     nan_list = []
        #     [nan_list.append(-9999) for x in range(0, num_cols, 1)]  # Create missing values for each column
        #     stats_df = pd.DataFrame(index=[bin_filedate], data=[nan_list],
        #                             columns=pd.MultiIndex.from_tuples(stats_coll_df.columns))

        # First file inits stats collection
        if filecounter == 1:
            stats_coll_df = rawdata_df.copy()
        else:
            # stats_coll_df = stats_coll_df.append(rawdata_df)
            stats_coll_df = pd.concat([stats_coll_df, rawdata_df], axis=0)

        return stats_coll_df

    def make_plot(self, df, outdir):
        """Plot aggregated values for each file"""
        self.logger.info(f"{self.section_id} Plotting aggregated data ...")
        df.replace(-9999, np.nan, inplace=True)
        df.sort_index(axis=1, inplace=True)  # lexsort for better performance
        df.sort_index(axis=0, inplace=True)

        # Get only var name, units and instrument from 3-row MultiIndex,
        # this means that the row with agg info is skipped here, but then used later during plotting
        vars = list(zip(df.columns.get_level_values(0),
                        df.columns.get_level_values(1),
                        df.columns.get_level_values(2)))
        vars = set(vars)

        for var in vars:
            self.logger.info(f"{self.section_id}    Plotting {var} ...")
            var_df = df[var].copy()
            gs = gridspec.GridSpec(2, 2)  # rows, cols
            gs.update(wspace=0.1, hspace=0, left=0.03, right=0.99, top=0.99, bottom=0.01)
            fig = plt.Figure(facecolor='white', figsize=(32, 9))
            ax1 = fig.add_subplot(gs[0, 0])
            ax2 = fig.add_subplot(gs[1, 0])

            ax1.plot_date(var_df.index, var_df['median'], alpha=.5, c='#455A64', label='median')
            ax1.fill_between(x=var_df.index, y1=var_df['q95'], y2=var_df['q05'],
                             alpha=.2, color='#5f87ae', label='5-95th percentile')
            ax1.errorbar(var_df.index, var_df['mean'], var_df['std'],
                         marker='o', mec='black', mfc='None', color='black', capsize=0,
                         label='mean +/- std', alpha=.2)
            try:
                ax1.set_ylim(var_df['q01'].min(), var_df['q99'].max())
            except ValueError:
                pass
            ax2.plot_date(var_df.index, var_df['count'], alpha=1, c='#37474F', label='count')

            text_args = dict(verticalalignment='top',
                             size=14, color='black', backgroundcolor='none', zorder=100)
            ax1.text(0.01, 0.96, f"{var[0]} {var[1]} {var[2]}", transform=ax1.transAxes, horizontalalignment='left',
                     **text_args)

            _default_format(ax=ax1, width=1, length=2, txt_ylabel=var[0], txt_ylabel_units=var[1])
            _default_format(ax=ax2, width=1, length=2, txt_ylabel='counts')

            # ahx.axhline(0, color='black', ls='-', lw=1, zorder=1)
            font = {'family': 'sans-serif', 'size': 10}
            ax1.legend(frameon=True, loc='upper right', prop=font).set_zorder(100)

            outfile = outdir / f"{var[0]}_{var[1]}_{var[2]}"
            fig.savefig(f"{outfile}.png", format='png', bbox_inches='tight', facecolor='w',
                        transparent=True, dpi=150)

    def get_filedate(self, fid):
        """Get filedate from filename"""
        rawdata_filedate = dt.datetime.strptime(fid, self.rawdata_file_datefrmt)
        self.logger.info(f"{self.section_id}    Filedate for {fid}: {rawdata_filedate}")
        return rawdata_filedate

    def q01(self, x):
        return x.quantile(0.01)

    def q05(self, x):
        return x.quantile(0.05)

    def q95(self, x):
        return x.quantile(0.95)

    def q99(self, x):
        return x.quantile(0.99)
