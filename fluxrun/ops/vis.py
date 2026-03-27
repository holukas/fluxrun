import datetime as dt
import os

import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import dates
from matplotlib.ticker import MultipleLocator

try:
    from .file import ReadEddyProFullOutputFile, read_uncompr_ascii_file
except ImportError:
    from file import ReadEddyProFullOutputFile, read_uncompr_ascii_file

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 15)
pd.set_option('display.max_rows', 20)

_P = {
    'ts':           '#3B82F6',  # blue        – time series line
    'ts_band':      '#DBEAFE',  # blue-100    – 5–95th percentile fill
    'daily':        '#F59E0B',  # amber       – daily mean/std
    'hist':         '#6366F1',  # indigo      – histogram bars
    'cumul':        '#10B981',  # emerald     – cumulative sum
    'cumul_fill':   '#D1FAE5',  # emerald-100 – cumulative fill
    'diurnal':      '#EC4899',  # pink        – diurnal cycle
    'diurnal_band': '#FCE7F3',  # pink-100    – diurnal std fill
    'agg_med':      '#334155',  # slate-700   – median line
    'agg_band':     '#BAE6FD',  # sky-200     – percentile fill
    'count':        '#64748B',  # slate-500   – count line
    'zero':         '#94A3B8',  # slate-400   – zero reference
    'text':         '#1E293B',  # slate-900   – titles / labels
    'subtext':      '#64748B',  # slate-500   – axis tick labels
    'spine':        '#CBD5E1',  # slate-300   – axis spines
    'grid':         '#F8FAFC',  # slate-50    – grid lines
    'statsbox':     '#F1F5F9',  # slate-100   – stats background
}


def _style_ax(ax, fontsize=7):
    """Apply clean, modern styling to an axis."""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(_P['spine'])
    ax.spines['bottom'].set_color(_P['spine'])
    ax.yaxis.grid(True, color=_P['grid'], linewidth=0.8, zorder=0)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)
    ax.set_facecolor('white')
    ax.tick_params(colors=_P['subtext'], labelsize=fontsize, length=3, width=0.7)
    ax.xaxis.label.set_color(_P['subtext'])
    ax.yaxis.label.set_color(_P['subtext'])


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

            fig = plt.figure(figsize=(12, 11), dpi=300, facecolor='white')
            var = col[0]
            units = col[1]

            self.logger.info(f"Working on: {col} (column #{ix} of {columns_count}) ...")
            plot_name = f"{ix}_{var}_{units}"
            plot_name = plot_name.replace('*', 'star')
            plot_name = plot_name.replace('/', '_over_')

            try:
                y = self.data_df[col].astype(float)
            except ValueError:
                self.logger.warning(f"SKIPPING PLOTTING FOR {col} BECAUSE IT IS NOT NUMERIC.")
                continue

            y = sanitize_y(y=y)

            # if qc flag available, filter for quality 0 and 1 fluxes, do not use quality 2 fluxes
            qc_col = (f"qc_{var}", '[#]')
            quality_controlled = 0  # 0 = no, 1 = yes
            if qc_col in columns_names:
                qc = self.data_df[qc_col] < 2  # qc = quality control flags, 0 = very good, 1 = OK
                y = y[qc]
                quality_controlled = 1

            if not y.empty:

                hs = 8   # heading size
                ls = 7   # label size

                fig.suptitle(f"{var}  {units}", fontsize=18, fontweight='bold',
                             color=_P['text'], x=0.02, ha='left', va='top', y=0.99)

                qua1 = y.quantile(0.01)
                qua2 = y.quantile(0.99)

                # TIME SERIES
                ax1 = plt.subplot2grid((6, 4), (0, 0), colspan=4, rowspan=2)
                ax1.fill_between(y.index, y.quantile(0.05), y.quantile(0.95),
                                 color=_P['ts_band'], alpha=0.7, label='5–95th pct', zorder=1)
                ax1.plot(y.index, y, color=_P['ts'], linewidth=0.35, alpha=0.9, zorder=2)
                _style_ax(ax1)
                ax1.set_xlabel("date", size=ls)
                ax1.set_ylabel(units, size=ls)
                ax1.set_title(f"{var}  ·  time series  (shading: 5–95th percentile)",
                              size=hs, fontweight='bold', color=_P['text'], loc='left', pad=6)
                ax1.xaxis.set_major_formatter(dates.DateFormatter("%d %b"))
                ax1.set_ylim(qua1, qua2)

                # DAILY MEAN
                ax4 = plt.subplot2grid((6, 4), (2, 0), colspan=2)
                daily_avg = y.resample('D').mean()
                daily_std = y.resample('D').std()
                ax4.fill_between(daily_avg.index, daily_avg - daily_std, daily_avg + daily_std,
                                 color=_P['daily'], alpha=0.18, zorder=1)
                ax4.scatter(daily_avg.index, daily_avg,
                            color=_P['daily'], s=8, zorder=3, edgecolors='none')
                ax4.axhline(0, color=_P['zero'], linewidth=0.7, alpha=0.6)
                _style_ax(ax4)
                ax4.set_xlabel("date", size=ls)
                ax4.set_ylabel(units, size=ls)
                ax4.set_title(f"{var}  ·  daily mean ± std",
                              size=hs, fontweight='bold', color=_P['text'], loc='left', pad=6)
                ax4.xaxis.set_major_formatter(dates.DateFormatter("%d %b"))
                ax4.set_ylim(qua1, qua2)

                # HISTOGRAM
                try:
                    ax2 = plt.subplot2grid((6, 4), (3, 0), colspan=2)
                    ax2.hist(y, bins=30, range=(qua1, qua2),
                             color=_P['hist'], edgecolor='white', linewidth=0.3, alpha=0.85)
                    _style_ax(ax2)
                    ax2.set_xlabel(units, size=ls)
                    ax2.set_ylabel("count", size=ls)
                    ax2.set_title(f"{var}  ·  distribution",
                                  size=hs, fontweight='bold', color=_P['text'], loc='left', pad=6)
                except ValueError as e:
                    self.logger.error(f"ERROR DURING HISTOGRAM PLOTTING: {e}")

                # CUMULATIVE
                ax5 = plt.subplot2grid((6, 4), (2, 2), colspan=2)
                cumsum = y.cumsum()
                ax5.fill_between(y.index, cumsum, alpha=0.15, color=_P['cumul'], zorder=1)
                ax5.plot(y.index, cumsum, color=_P['cumul'], linewidth=0.8, zorder=2)
                ax5.axhline(0, color=_P['zero'], linewidth=0.7, alpha=0.6)
                _style_ax(ax5)
                ax5.set_xlabel("date", size=ls)
                ax5.set_ylabel(units, size=ls)
                ax5.set_title(f"{var}  ·  cumulative sum",
                              size=hs, fontweight='bold', color=_P['text'], loc='left', pad=6)
                ax5.xaxis.set_major_formatter(dates.DateFormatter("%d %b"))

                # DIURNAL CYCLE
                ax6 = plt.subplot2grid((6, 4), (3, 2), colspan=1)
                hourly_avg = y.groupby(y.index.hour).mean()
                hourly_std = y.groupby(y.index.hour).std()
                ax6.fill_between(hourly_avg.index, hourly_avg - hourly_std, hourly_avg + hourly_std,
                                 color=_P['diurnal_band'], alpha=0.9, zorder=1)
                ax6.plot(hourly_avg.index, hourly_avg, color=_P['diurnal'], linewidth=1.2, zorder=2)
                ax6.axhline(0, color=_P['zero'], linewidth=0.7, alpha=0.6)
                _style_ax(ax6)
                ax6.set_xlabel("hour (UTC)", size=ls)
                ax6.set_ylabel(units, size=ls)
                ax6.set_title(f"{var}  ·  diurnal cycle",
                              size=hs, fontweight='bold', color=_P['text'], loc='left', pad=6)
                ax6.set_xlim(0, 23)
                ax6.xaxis.set_major_locator(MultipleLocator(6))

                # STATS BOX
                info_dict = y.describe()
                lines = [
                    f"n      {info_dict['count']:.0f}",
                    f"mean   {info_dict['mean']:.4g}",
                    f"std    {info_dict['std']:.4g}",
                    f"p05    {y.quantile(0.05):.4g}",
                    f"p50    {info_dict['50%']:.4g}",
                    f"p95    {y.quantile(0.95):.4g}",
                    f"min    {info_dict['min']:.4g}",
                    f"max    {info_dict['max']:.4g}",
                ]
                if quality_controlled:
                    lines.append(f"\nQC filtered  (qc < 2)")

                ax_s = plt.subplot2grid((6, 4), (3, 3))
                ax_s.axis('off')
                ax_s.text(0.08, 0.95, "\n".join(lines),
                          transform=ax_s.transAxes, fontsize=6.5,
                          verticalalignment='top', fontfamily='monospace',
                          color=_P['text'],
                          bbox=dict(boxstyle='round,pad=0.5', facecolor=_P['statsbox'],
                                    edgecolor=_P['spine'], linewidth=0.8))

                # FINGERPRINT HEATMAP
                ax_fp = plt.subplot2grid((6, 4), (4, 0), colspan=4, rowspan=2)
                fp = y.copy().to_frame(name='v')
                fp['date'] = fp.index.date
                fp['slot'] = fp.index.hour * 2 + fp.index.minute // 30  # 0–47 half-hour slots
                fp_pivot = fp.pivot_table(index='date', columns='slot', values='v', aggfunc='mean')

                im = ax_fp.pcolormesh(
                    np.arange(fp_pivot.shape[1] + 1),
                    np.arange(fp_pivot.shape[0] + 1),
                    np.ma.masked_invalid(fp_pivot.values),
                    cmap='RdYlBu_r',
                    vmin=qua1, vmax=qua2,
                    shading='flat',
                )
                cbar = fig.colorbar(im, ax=ax_fp, pad=0.01, fraction=0.015, aspect=40)
                cbar.ax.tick_params(labelsize=6)
                cbar.set_label(units, size=ls)

                # X-axis: every 2 hours
                x_ticks = list(range(0, 48, 4))
                ax_fp.set_xticks([s + 0.5 for s in x_ticks])
                ax_fp.set_xticklabels(
                    [f"{s // 2:02d}:{(s % 2) * 30:02d}" for s in x_ticks], size=ls)

                # Y-axis: dates, thinned to ~15 labels max
                n_dates = fp_pivot.shape[0]
                step = max(1, n_dates // 15)
                y_ticks = list(range(0, n_dates, step))
                ax_fp.set_yticks([p + 0.5 for p in y_ticks])
                ax_fp.set_yticklabels(
                    [str(fp_pivot.index[p]) for p in y_ticks], size=ls)

                ax_fp.set_xlabel("time (UTC)", size=ls)
                ax_fp.set_ylabel("date", size=ls)
                ax_fp.set_title(f"{var}  ·  fingerprint",
                                size=hs, fontweight='bold', color=_P['text'], loc='left', pad=6)
                ax_fp.spines['top'].set_visible(False)
                ax_fp.spines['right'].set_visible(False)
                ax_fp.spines['left'].set_color(_P['spine'])
                ax_fp.spines['bottom'].set_color(_P['spine'])
                ax_fp.tick_params(colors=_P['subtext'], labelsize=ls, length=3, width=0.7)
                ax_fp.xaxis.label.set_color(_P['subtext'])
                ax_fp.yaxis.label.set_color(_P['subtext'])

                plt.tight_layout(pad=1.2, rect=[0, 0, 1, 0.97])
                plot_name = os.path.join(self.plot_folder, plot_name)
                self.logger.info(f"    --> Saving plot {plot_name} ...")
                plt.savefig(plot_name + '.png', dpi=150, facecolor='white')
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
        self.settings = settings_dict
        self.logger = logger
        self.rawdata_file_datefrmt = rawdata_file_datefrmt

        self.collect_aggs()

    def collect_aggs(self):
        """Loop"""
        filecounter = 0
        stats_coll_df = pd.DataFrame()
        num_files = len(self.rawdata_found_files_dict)
        for fid, filepath in self.rawdata_found_files_dict.items():
            try:
                filecounter += 1
                self.file_header_for_log(fid=fid, num_files=num_files, filecounter=filecounter)
                rawdata_filedate = self.get_filedate(fid)
                rawdata_df = read_uncompr_ascii_file(
                    settings=self.settings,
                    filepath=filepath,
                    logger=self.logger,
                    section_id=self.section_id
                )
                stats_coll_df = self.calc_rawdata_stats(rawdata_df=rawdata_df,
                                                        rawdata_filedate=rawdata_filedate,
                                                        stats_coll_df=stats_coll_df,
                                                        filecounter=filecounter)
            except Exception as e:
                self.logger.error(e)
                raise Exception(f"ERROR IN FILE {filepath}: {e}")

        self.make_plot(df=stats_coll_df,
                       outdir=self.settings['_dir_out_run_plots_aggregates_rawdata'])

    def file_header_for_log(self, fid, num_files, filecounter):
        spacer = "=" * 30
        self.logger.info(f"{self.section_id} {spacer}")
        self.logger.info(f"{self.section_id} File {fid} (#{filecounter} of {num_files}) ...")
        self.logger.info(f"{self.section_id} {spacer}")

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
        _vars = list(zip(df.columns.get_level_values(0),
                         df.columns.get_level_values(1),
                         df.columns.get_level_values(2)))
        _vars = set(_vars)

        for var in _vars:
            self.logger.info(f"{self.section_id}    Plotting {var} ...")
            var_df = df[var].copy()
            gs = gridspec.GridSpec(2, 1, hspace=0.08, left=0.05, right=0.99, top=0.96, bottom=0.06)
            fig = plt.Figure(facecolor='white', figsize=(32, 9))
            ax1 = fig.add_subplot(gs[0])
            ax2 = fig.add_subplot(gs[1])

            ax1.fill_between(x=var_df.index, y1=var_df['q05'], y2=var_df['q95'],
                             alpha=0.25, color=_P['agg_band'], label='5–95th percentile', zorder=1)
            ax1.plot(var_df.index, var_df['median'],
                     alpha=0.8, color=_P['agg_med'], linewidth=0.8, label='median', zorder=3)
            ax1.errorbar(var_df.index, var_df['mean'], var_df['std'],
                         marker='o', mec=_P['daily'], mfc='none', color=_P['daily'],
                         capsize=0, label='mean ± std', alpha=0.4, markersize=3,
                         linewidth=0, elinewidth=1.2, zorder=2)
            try:
                ax1.set_ylim(var_df['q01'].min(), var_df['q99'].max())
            except ValueError:
                pass

            ax2.fill_between(var_df.index, var_df['count'],
                             alpha=0.3, color=_P['count'], zorder=1)
            ax2.plot(var_df.index, var_df['count'],
                     alpha=0.9, color=_P['count'], linewidth=0.8, zorder=2)

            ax1.text(0.005, 0.97, f"{var[0]}  {var[1]}  {var[2]}",
                     transform=ax1.transAxes, horizontalalignment='left',
                     verticalalignment='top', size=13, color=_P['text'],
                     fontweight='bold', backgroundcolor='none', zorder=100)

            _style_ax(ax1, fontsize=11)
            _style_ax(ax2, fontsize=11)
            ax1.set_ylabel(f"{var[0]}  {var[1]}", color=_P['subtext'], fontsize=11)
            ax2.set_ylabel("count", color=_P['subtext'], fontsize=11)
            ax2.set_xlabel("file date", color=_P['subtext'], fontsize=11)

            font = {'family': 'sans-serif', 'size': 10}
            ax1.legend(frameon=False, loc='upper right', prop=font).set_zorder(100)

            outname = f"{var[0]}_{var[1]}_{var[2]}"
            outname = outname.replace(':', '_')
            outfile = outdir / outname
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


if __name__ == '__main__':
    import logging
    import tempfile
    from pathlib import Path

    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    _logger = logging.getLogger('vis_test')

    _outdir = Path(tempfile.mkdtemp())
    print(f"Output directory: {_outdir}")

    # 30 days of 30-minute data
    _dates = pd.date_range('2025-06-01', periods=30 * 48, freq='30T')
    _rng = np.random.default_rng(42)
    _n = len(_dates)
    _hour = _dates.hour + _dates.minute / 60

    # Diurnal patterns with noise
    _co2 = -8 * np.sin(np.pi * (_hour - 6) / 12) + _rng.normal(0, 1.5, _n)
    _h = 250 * np.sin(np.pi * (_hour - 6) / 12) + _rng.normal(0, 20, _n)
    _qc_co2 = _rng.choice([0, 1, 2], size=_n, p=[0.7, 0.2, 0.1])

    _cols = pd.MultiIndex.from_tuples([
        ('co2_flux', '[µmolm-2s-1]'),
        ('qc_co2_flux', '[#]'),
        ('H', '[Wm-2]'),
    ])
    _dummy_df = pd.DataFrame(
        np.column_stack([_co2, _qc_co2, _h]),
        index=_dates,
        columns=_cols,
    )

    _plotter = PlotEddyProFullOutputFile(
        file_to_plot=None,
        destination_folder=_outdir,
        logger=_logger,
    )
    _plotter.data_df = _dummy_df
    _columns_names, _columns_count = _plotter.col_info()
    _plotter.plot_full_output(_columns_count, _columns_names)
    print(f"Done. Plots saved to: {_outdir}")
