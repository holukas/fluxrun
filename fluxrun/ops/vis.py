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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Plot Configuration Constants
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PlotConfig:
    """Configuration constants for plot styling and sizing."""
    # Summary plots (PlotEddyProFullOutputFile)
    SUMMARY_FIGSIZE = (12, 11)
    SUMMARY_DPI = 150
    SUMMARY_HEADING_FONTSIZE = 8
    SUMMARY_LABEL_FONTSIZE = 7

    # Time series
    TS_LINEWIDTH = 0.35
    TS_ALPHA = 0.9
    TS_BAND_ALPHA = 0.7

    # Daily mean
    DAILY_BAND_ALPHA = 0.18
    DAILY_SCATTER_SIZE = 8

    # Histogram
    HIST_BINS = 30
    HIST_ALPHA = 0.85

    # Cumulative
    CUMUL_LINEWIDTH = 0.8
    CUMUL_BAND_ALPHA = 0.15

    # Diurnal cycle
    DIURNAL_LINEWIDTH = 1.2
    DIURNAL_BAND_ALPHA = 0.9
    DIURNAL_MAX_HOUR = 23
    DIURNAL_HOUR_LOCATOR = 6

    # Fingerprint heatmap
    FINGERPRINT_CMAP = 'RdYlBu_r'
    FINGERPRINT_MAX_LABELS = 15
    FINGERPRINT_COLORBAR_FRACTION = 0.015
    FINGERPRINT_COLORBAR_PAD = 0.01
    FINGERPRINT_COLORBAR_ASPECT = 40
    FINGERPRINT_COLORBAR_FONTSIZE = 6

    # Aggregate plots
    AGG_FIGSIZE = (32, 9)
    AGG_FONTSIZE = 11
    AGG_TEXT_SIZE = 13
    AGG_GRID_HSPACE = 0.08
    AGG_GRID_LEFT = 0.05
    AGG_GRID_RIGHT = 0.99
    AGG_GRID_TOP = 0.96
    AGG_GRID_BOTTOM = 0.06


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
        if last_date.day - first_date.day < 5:  # if we have less than 5 days of data add dates to avoid problems with results plotting
            last_date = last_date + pd.offsets.Day(20)
            self.logger.debug(f"Date range: {first_date} to {last_date} (extended +20 days for plotting)")
        else:
            self.logger.debug(f"Date range: {first_date} to {last_date}")
        # generate continuous date range and re-index data
        filled_date_range = pd.date_range(first_date, last_date, freq='30min')
        df = df.reindex(filled_date_range, fill_value=-9999)  # apply new continuous index to data
        return df

    def col_info(self):
        # read columns names from file, count columns in file
        columns_names = self.data_df.columns
        columns_count = len(self.data_df.columns)
        self.logger.debug(f"Found {columns_count} columns to process")
        return columns_names, columns_count

    def _prepare_plot_data(self, col, columns_names):
        """Validate and prepare column data for plotting."""
        try:
            y = self.data_df[col].astype(float)
        except ValueError:
            self.logger.warning(f"Skipping {col[0]} — not numeric")
            return None, None

        y = sanitize_y(y=y)

        # if qc flag available, filter for quality 0 and 1 fluxes, do not use quality 2 fluxes
        qc_col = (f"qc_{col[0]}", '[#]')
        quality_controlled = False
        if qc_col in columns_names:
            qc = self.data_df[qc_col] < 2  # qc = quality control flags, 0 = very good, 1 = OK
            y = y[qc]
            quality_controlled = True

        return y, quality_controlled if y.empty is False else (None, None)

    def _plot_time_series(self, ax, y, quantiles, units, var, heading_size, label_size):
        """Plot time series with percentile bands."""
        ax.fill_between(y.index, quantiles[0.05], quantiles[0.95],
                        color=_P['ts_band'], alpha=PlotConfig.TS_BAND_ALPHA, label='5–95th pct', zorder=1)
        ax.plot(y.index, y, color=_P['ts'], linewidth=PlotConfig.TS_LINEWIDTH, alpha=PlotConfig.TS_ALPHA, zorder=2)
        _style_ax(ax)
        ax.set_xlabel("date", size=label_size)
        ax.set_ylabel(units, size=label_size)
        ax.set_title(f"{var}  ·  time series  (shading: 5–95th percentile)",
                     size=heading_size, fontweight='bold', color=_P['text'], loc='left', pad=6)
        ax.xaxis.set_major_formatter(dates.DateFormatter("%d %b"))

    def _plot_daily_mean(self, ax, y, quantiles, units, var, heading_size, label_size, q_min, q_max):
        """Plot daily mean with standard deviation."""
        daily_resampled = y.resample('D')
        daily_avg = daily_resampled.mean()
        daily_std = daily_resampled.std()
        ax.fill_between(daily_avg.index, daily_avg - daily_std, daily_avg + daily_std,
                        color=_P['daily'], alpha=PlotConfig.DAILY_BAND_ALPHA, zorder=1)
        ax.scatter(daily_avg.index, daily_avg,
                   color=_P['daily'], s=PlotConfig.DAILY_SCATTER_SIZE, zorder=3, edgecolors='none')
        ax.axhline(0, color=_P['zero'], linewidth=0.7, alpha=0.6)
        _style_ax(ax)
        ax.set_xlabel("date", size=label_size)
        ax.set_ylabel(units, size=label_size)
        ax.set_title(f"{var}  ·  daily mean ± std",
                     size=heading_size, fontweight='bold', color=_P['text'], loc='left', pad=6)
        ax.xaxis.set_major_formatter(dates.DateFormatter("%d %b"))
        ax.set_ylim(q_min, q_max)

    def _plot_histogram(self, ax, y, quantiles, units, var, heading_size, label_size, q_min, q_max):
        """Plot histogram of data distribution."""
        try:
            ax.hist(y, bins=PlotConfig.HIST_BINS, range=(q_min, q_max),
                    color=_P['hist'], edgecolor='white', linewidth=0.3, alpha=PlotConfig.HIST_ALPHA)
            _style_ax(ax)
            ax.set_xlabel(units, size=label_size)
            ax.set_ylabel("count", size=label_size)
            ax.set_title(f"{var}  ·  distribution",
                         size=heading_size, fontweight='bold', color=_P['text'], loc='left', pad=6)
        except ValueError as e:
            self.logger.error(f"ERROR DURING HISTOGRAM PLOTTING: {e}")

    def _plot_cumulative(self, ax, y, units, var, heading_size, label_size, q_min, q_max):
        """Plot cumulative sum."""
        cumsum = y.cumsum()
        ax.fill_between(y.index, cumsum, alpha=PlotConfig.CUMUL_BAND_ALPHA, color=_P['cumul'], zorder=1)
        ax.plot(y.index, cumsum, color=_P['cumul'], linewidth=PlotConfig.CUMUL_LINEWIDTH, zorder=2)
        ax.axhline(0, color=_P['zero'], linewidth=0.7, alpha=0.6)
        _style_ax(ax)
        ax.set_xlabel("date", size=label_size)
        ax.set_ylabel(units, size=label_size)
        ax.set_title(f"{var}  ·  cumulative sum",
                     size=heading_size, fontweight='bold', color=_P['text'], loc='left', pad=6)
        ax.xaxis.set_major_formatter(dates.DateFormatter("%d %b"))

    def _plot_diurnal(self, ax, y, units, var, heading_size, label_size):
        """Plot diurnal (hourly) cycle."""
        hourly_resampled = y.groupby(y.index.hour)
        hourly_avg = hourly_resampled.mean()
        hourly_std = hourly_resampled.std()
        ax.fill_between(hourly_avg.index, hourly_avg - hourly_std, hourly_avg + hourly_std,
                        color=_P['diurnal_band'], alpha=PlotConfig.DIURNAL_BAND_ALPHA, zorder=1)
        ax.plot(hourly_avg.index, hourly_avg, color=_P['diurnal'], linewidth=PlotConfig.DIURNAL_LINEWIDTH, zorder=2)
        ax.axhline(0, color=_P['zero'], linewidth=0.7, alpha=0.6)
        _style_ax(ax)
        ax.set_xlabel("hour", size=label_size)
        ax.set_ylabel(units, size=label_size)
        ax.set_title(f"{var}  ·  diurnal cycle",
                     size=heading_size, fontweight='bold', color=_P['text'], loc='left', pad=6)
        ax.set_xlim(0, PlotConfig.DIURNAL_MAX_HOUR)
        ax.xaxis.set_major_locator(MultipleLocator(PlotConfig.DIURNAL_HOUR_LOCATOR))

    def _plot_fingerprint(self, ax_fingerprint, y, quantiles, units, var, heading_size, label_size, fig, q_min, q_max):
        """Plot fingerprint heatmap (time-of-day vs date)."""
        fingerprint_df = y.copy().to_frame(name='v')
        fingerprint_df['date'] = fingerprint_df.index.date
        fingerprint_df['slot'] = fingerprint_df.index.hour * 2 + fingerprint_df.index.minute // 30
        fingerprint_pivot = fingerprint_df.pivot_table(index='date', columns='slot', values='v', aggfunc='mean')

        im = ax_fingerprint.pcolormesh(
            np.arange(fingerprint_pivot.shape[1] + 1),
            np.arange(fingerprint_pivot.shape[0] + 1),
            np.ma.masked_invalid(fingerprint_pivot.values),
            cmap=PlotConfig.FINGERPRINT_CMAP,
            vmin=q_min, vmax=q_max,
            shading='flat',
        )
        cbar = fig.colorbar(im, ax=ax_fingerprint, pad=PlotConfig.FINGERPRINT_COLORBAR_PAD,
                           fraction=PlotConfig.FINGERPRINT_COLORBAR_FRACTION, aspect=PlotConfig.FINGERPRINT_COLORBAR_ASPECT)
        cbar.ax.tick_params(labelsize=PlotConfig.FINGERPRINT_COLORBAR_FONTSIZE)
        cbar.set_label(units, size=label_size)

        # X-axis: every 2 hours
        x_ticks = list(range(0, 48, 4))
        ax_fingerprint.set_xticks([s + 0.5 for s in x_ticks])
        ax_fingerprint.set_xticklabels(
            [f"{s // 2:02d}:{(s % 2) * 30:02d}" for s in x_ticks], size=label_size)

        # Y-axis: dates, thinned to ~15 labels max
        n_dates = fingerprint_pivot.shape[0]
        step = max(1, n_dates // PlotConfig.FINGERPRINT_MAX_LABELS)
        y_ticks = list(range(0, n_dates, step))
        ax_fingerprint.set_yticks([p + 0.5 for p in y_ticks])
        ax_fingerprint.set_yticklabels(
            [str(fingerprint_pivot.index[p]) for p in y_ticks], size=label_size)

        ax_fingerprint.set_xlabel("time (UTC)", size=label_size)
        ax_fingerprint.set_ylabel("date", size=label_size)
        ax_fingerprint.set_title(f"{var}  ·  fingerprint",
                               size=heading_size, fontweight='bold', color=_P['text'], loc='left', pad=6)
        _style_ax(ax_fingerprint)

    def _create_stats_box(self, fig, y, quantiles, var, quality_controlled, heading_size, label_size):
        """Create statistics box with summary statistics."""
        info_dict = y.describe()
        lines = [
            f"n      {info_dict['count']:.0f}",
            f"mean   {info_dict['mean']:.4g}",
            f"std    {info_dict['std']:.4g}",
            f"p05    {quantiles[0.05]:.4g}",
            f"p50    {quantiles[0.50]:.4g}",
            f"p95    {quantiles[0.95]:.4g}",
            f"min    {info_dict['min']:.4g}",
            f"max    {info_dict['max']:.4g}",
        ]
        if quality_controlled:
            lines.append(f"\nQC filtered  (qc < 2)")

        ax_stats = plt.subplot2grid((6, 4), (3, 3))
        ax_stats.axis('off')
        ax_stats.text(0.08, 0.95, "\n".join(lines),
                      transform=ax_stats.transAxes, fontsize=6.5,
                      verticalalignment='top', fontfamily='monospace',
                      color=_P['text'],
                      bbox=dict(boxstyle='round,pad=0.5', facecolor=_P['statsbox'],
                                edgecolor=_P['spine'], linewidth=0.8))

    def plot_full_output(self, columns_count, columns_names):
        """Assemble summary plots for each column."""
        self.logger.info(f"Generating plots for {columns_count} columns...")

        for ix, col in enumerate(self.data_df.columns):
            var = col[0]
            units = col[1]

            self.logger.debug(f"Processing column {ix + 1}/{columns_count}: {var}")

            # Prepare and validate data
            y, quality_controlled = self._prepare_plot_data(col, columns_names)
            if y is None:
                continue

            # Create figure and setup
            fig = plt.figure(figsize=PlotConfig.SUMMARY_FIGSIZE, dpi=PlotConfig.SUMMARY_DPI, facecolor='white')
            fig.suptitle(f"{var}  {units}", fontsize=18, fontweight='bold',
                         color=_P['text'], x=0.02, ha='left', va='top', y=0.99)

            heading_size = PlotConfig.SUMMARY_HEADING_FONTSIZE
            label_size = PlotConfig.SUMMARY_LABEL_FONTSIZE
            quantiles = y.quantile([0.01, 0.05, 0.50, 0.95, 0.99])
            q_min, q_max = quantiles[0.01], quantiles[0.99]

            # Create subplot axes
            ax1 = plt.subplot2grid((6, 4), (0, 0), colspan=4, rowspan=2)
            ax2 = plt.subplot2grid((6, 4), (3, 0), colspan=2)
            ax4 = plt.subplot2grid((6, 4), (2, 0), colspan=2)
            ax5 = plt.subplot2grid((6, 4), (2, 2), colspan=2)
            ax6 = plt.subplot2grid((6, 4), (3, 2), colspan=1)
            ax_fingerprint = plt.subplot2grid((6, 4), (4, 0), colspan=4, rowspan=2)

            # Generate all plots using helper methods
            self._plot_time_series(ax1, y, quantiles, units, var, heading_size, label_size)
            ax1.set_ylim(q_min, q_max)
            self._plot_daily_mean(ax4, y, quantiles, units, var, heading_size, label_size, q_min, q_max)
            self._plot_histogram(ax2, y, quantiles, units, var, heading_size, label_size, q_min, q_max)
            self._plot_cumulative(ax5, y, units, var, heading_size, label_size, q_min, q_max)
            self._plot_diurnal(ax6, y, units, var, heading_size, label_size)
            self._create_stats_box(fig, y, quantiles, var, quality_controlled, heading_size, label_size)
            self._plot_fingerprint(ax_fingerprint, y, quantiles, units, var, heading_size, label_size, fig, q_min, q_max)

            # Save figure
            plt.tight_layout(pad=1.2, rect=[0, 0, 1, 0.97])
            plot_name = f"{ix}_{var}_{units}"
            plot_name = plot_name.replace('*', 'star').replace('/', '_over_')
            plot_path = os.path.join(self.plot_folder, plot_name)
            self.logger.debug(f"Saving plot: {plot_path}.png")
            plt.savefig(plot_path + '.png', dpi=PlotConfig.SUMMARY_DPI, facecolor='white')
            plt.close(fig)

        self.logger.info("Summary plots generation complete")


def availability_rawdata(rawdata_found_files_dict, rawdata_file_datefrmt, outdir, logger):
    """
    Plot data availability from datetime info in filenames

    Kudos:
        https://matplotlib.org/3.2.2/gallery/images_contours_and_fields/image_annotated_heatmap.html
    """

    logger.info("Plotting availability heatmap ...")

    # Prepare data for plot
    records = []
    for rawdata_file, rawdata_filepath in rawdata_found_files_dict.items():
        rawdata_filebin_filedate = dt.datetime.strptime(rawdata_filepath.name, rawdata_file_datefrmt)
        records.append({
            'datetime': rawdata_filebin_filedate,
            'date': rawdata_filebin_filedate.date(),
            'filesize': os.path.getsize(rawdata_filepath) / 1_000_000,  # in MB
        })
    plot_df = pd.DataFrame(records).set_index('datetime')

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
        self.logger.debug(f"Processing file {filecounter}/{num_files}: {fid}")

    def calc_rawdata_stats(self, rawdata_df, stats_coll_df, rawdata_filedate, filecounter):
        """Calculate stats for raw data"""

        if rawdata_df.empty:
            # In case there are no data, create df with one row of NaNs
            rawdata_df = pd.DataFrame(index=[0], columns=rawdata_df.columns)

        # Replace missing values -9999 with NaNs for correct stats calcs
        rawdata_df.replace(-9999, np.nan, inplace=True)

        rawdata_df['index'] = rawdata_filedate
        rawdata_df.sort_index(axis=1, inplace=True)  # lexsort for better performance
        aggs = ['count', 'min', 'max', 'mean', 'std', 'median', self.q01, self.q05, self.q95, self.q99]
        rawdata_df = rawdata_df.groupby('index').agg(aggs)

        # First file inits stats collection
        if filecounter == 1:
            stats_coll_df = rawdata_df.copy()
        else:
            stats_coll_df = pd.concat([stats_coll_df, rawdata_df], axis=0)

        return stats_coll_df

    def _plot_aggregate_data(self, ax, var_df, var):
        """Plot aggregated data with percentile bands, median, and mean ± std."""
        ax.fill_between(x=var_df.index, y1=var_df['q05'], y2=var_df['q95'],
                        alpha=0.25, color=_P['agg_band'], label='5–95th percentile', zorder=1)
        ax.plot(var_df.index, var_df['median'],
                alpha=0.8, color=_P['agg_med'], linewidth=0.8, label='median', zorder=3)
        ax.errorbar(var_df.index, var_df['mean'], var_df['std'],
                    marker='o', mec=_P['daily'], mfc='none', color=_P['daily'],
                    capsize=0, label='mean ± std', alpha=0.4, markersize=3,
                    linewidth=0, elinewidth=1.2, zorder=2)
        try:
            ax.set_ylim(var_df['q01'].min(), var_df['q99'].max())
        except ValueError:
            pass

    def _plot_aggregate_count(self, ax, var_df):
        """Plot count data."""
        ax.fill_between(var_df.index, var_df['count'],
                        alpha=0.3, color=_P['count'], zorder=1)
        ax.plot(var_df.index, var_df['count'],
                alpha=0.9, color=_P['count'], linewidth=0.8, zorder=2)

    def _format_aggregate_axes(self, ax1, ax2, var):
        """Format axes styling, labels, and legend."""
        ax1.text(0.005, 0.97, f"{var[0]}  {var[1]}  {var[2]}",
                 transform=ax1.transAxes, horizontalalignment='left',
                 verticalalignment='top', size=PlotConfig.AGG_TEXT_SIZE, color=_P['text'],
                 fontweight='bold', backgroundcolor='none', zorder=100)

        _style_ax(ax1, fontsize=PlotConfig.AGG_FONTSIZE)
        _style_ax(ax2, fontsize=PlotConfig.AGG_FONTSIZE)
        ax1.set_ylabel(f"{var[0]}  {var[1]}", color=_P['subtext'], fontsize=PlotConfig.AGG_FONTSIZE)
        ax2.set_ylabel("count", color=_P['subtext'], fontsize=PlotConfig.AGG_FONTSIZE)
        ax2.set_xlabel("file date", color=_P['subtext'], fontsize=PlotConfig.AGG_FONTSIZE)

        font = {'family': 'sans-serif', 'size': 10}
        ax1.legend(frameon=False, loc='upper right', prop=font).set_zorder(100)

    def make_plot(self, df, outdir):
        """Plot aggregated values for each file."""
        self.logger.debug("Generating aggregate plots...")
        df.replace(-9999, np.nan, inplace=True)
        df.sort_index(axis=1, inplace=True)  # lexsort for better performance
        df.sort_index(axis=0, inplace=True)

        # Get only var name, units and instrument from 3-row MultiIndex
        variables = list(zip(df.columns.get_level_values(0),
                         df.columns.get_level_values(1),
                         df.columns.get_level_values(2)))
        variables = set(variables)

        for var in variables:
            self.logger.debug(f"Plotting {var[0]}")
            var_df = df[var].copy()

            # Create figure with grid layout
            gs = gridspec.GridSpec(2, 1, hspace=PlotConfig.AGG_GRID_HSPACE, left=PlotConfig.AGG_GRID_LEFT,
                                  right=PlotConfig.AGG_GRID_RIGHT, top=PlotConfig.AGG_GRID_TOP, bottom=PlotConfig.AGG_GRID_BOTTOM)
            fig = plt.Figure(facecolor='white', figsize=PlotConfig.AGG_FIGSIZE)
            ax1 = fig.add_subplot(gs[0])
            ax2 = fig.add_subplot(gs[1])

            # Generate plots
            self._plot_aggregate_data(ax1, var_df, var)
            self._plot_aggregate_count(ax2, var_df)
            self._format_aggregate_axes(ax1, ax2, var)

            # Save figure
            outname = f"{var[0]}_{var[1]}_{var[2]}".replace(':', '_')
            outfile = outdir / outname
            fig.savefig(f"{outfile}.png", format='png', bbox_inches='tight', facecolor='w',
                        transparent=True, dpi=150)

    def get_filedate(self, fid):
        """Get filedate from filename"""
        rawdata_filedate = dt.datetime.strptime(fid, self.rawdata_file_datefrmt)
        self.logger.debug(f"Filedate: {rawdata_filedate}")
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
    _dates = pd.date_range('2025-06-01', periods=30 * 48, freq='30min')
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
