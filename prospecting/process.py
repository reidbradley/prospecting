

import logging
log = logging.getLogger('prospecting.process')
import pandas as pd


def clean_data(dataframe, metadata):
    log.info("Cleaning data...")
    tmp_df = dataframe.copy()
    tmp_df = drop_rows_with_na(tmp_df,metadata, copy=False)
    tmp_df = derive_to_bool(tmp_df,metadata, copy=False)
    tmp_df = drop_columns(tmp_df,metadata, copy=False)
    tmp_df = strip(tmp_df, metadata, copy=False)
    tmp_df = date_to_ordinal(tmp_df,metadata, copy=False)
    tmp_df = float_to_object(tmp_df,metadata, copy=False)
    tmp_df = zfill_col(tmp_df, metadata, copy=False)
    tmp_df = fill_na_with(tmp_df, metadata, copy=False)
    tmp_df = replace(tmp_df, metadata, copy=False)
    tmp_df = str_to_int(tmp_df, metadata, copy=False)
    tmp_df = object_to_int(tmp_df, metadata, copy=False)
    tmp_df = object_to_float(tmp_df, metadata, copy=False)
    tmp_df = float_to_int(tmp_df, metadata, copy=False)
    tmp_df.__name__ = 'df_clean'
    log.info("Data cleaned...")
    return tmp_df


def drop_rows_with_na(tmpdf, metadata, copy=True):
    if copy is True:
        tmpdf = tmpdf.copy()
    cols = metadata[metadata['drop_rows_with_na'].isin(["1"])]['column_name'].tolist()
    log.info("Dropping rows with NA for columns {0}".format(cols))
    return (tmpdf.dropna(subset=[cols]))


def derive_to_bool(tmpdf, metadata, copy=True):
    if copy is True:
        tmpdf = tmpdf.copy()
    cols = metadata[metadata['derive_to_bool'].isin(["1"])]['column_name'].tolist()
    tmpdf = tmpdf
    for col in cols:
        log.info("Deriving {0} to bool...".format(col))
        newcolname = (col + '_bool')
        tmpdf[newcolname] = tmpdf.loc[:,col].notnull()
        del tmpdf[col]
    return (tmpdf)


def strip(tmpdf, metadata, copy=True):
    if copy is True:
        tmpdf = tmpdf.copy()
    cols = metadata[metadata['strip_chars'].isin(["1"])]['column_name'].tolist()
    for col in cols:
        chars = metadata[metadata['column_name'] == col]['chars_to_strip'].item()
        log.info("Stripping {0} from {1}...".format(chars, col))
        tmpdf[col] = tmpdf.loc[:,col].str.strip(chars)
    return (tmpdf)


def drop_columns(tmpdf, metadata, copy=True):
    if copy is True:
        tmpdf = tmpdf.copy()
    cols = metadata[metadata['keep_flag'].isin(["0"])]['column_name'].tolist()
    return(tmpdf.drop(labels=cols, axis=1))


def date_to_ordinal(tmpdf, metadata, copy=True):
    if copy is True:
        tmpdf = tmpdf.copy()
    cols = metadata[metadata['date_to_ordinal'].isin(["1"])]['column_name'].tolist()
    for col in cols:
        log.info("Converting {0} date to ordinal...".format(col))
        tmpdf[col] = [date.toordinal() for date in tmpdf[col]]
    return (tmpdf)


def zfill_col(tmpdf, metadata, copy=True):
    if copy is True:
        tmpdf = tmpdf.copy()
    cols = metadata[metadata['zfill_col'].isin(["1"])]['column_name'].tolist()
    for col in cols:
        z = metadata[metadata['column_name'] == col]['z'].item()
        log.info("zfilling column {0} with {1}".format(col, z))
        tmpdf[col] = [str(row).zfill(int(z)) for row in tmpdf.loc[:, col]]
    return (tmpdf)


def fill_na_with(tmpdf, metadata, copy=True):
    if copy is True:
        tmpdf = tmpdf.copy()
    cols = metadata[metadata['fill_na'].isin(["1"])]['column_name'].tolist()
    log.info("Filling columns with NA")
    for col in cols:
        fill_with = metadata[metadata['column_name'] == col]['fill_na_with'].item()
        if fill_with == 'TRUE':
            fill = True
        if fill_with == 'FALSE':
            fill = False
        if fill_with == '0':
            fill = 0
        tmpdf[col] = tmpdf[col].fillna(fill)
    return (tmpdf)


def replace(tmpdf, metadata, copy=True):
    if copy is True:
        tmpdf = tmpdf.copy()
    regex_groups = [i for i in set(metadata['regex_group']) if i is not '0']
    for group in regex_groups:
        cols = metadata[metadata['regex_group'].isin([group])]['column_name'].tolist()
        regex = [r for i in set(metadata[metadata['regex_group'].isin([group])]['regex']) for r in i.split(" | ")]
        regex_replace = [rr for i in set(metadata[metadata['regex_group'].isin([group])]['regex_replace']) for rr in i.split(" | ")]
        log.info("Replacing column group {0} regex {1} with {2}".format(group, regex, regex_replace))
        for col in cols:
            tmpdf[col] = tmpdf.loc[:, col].replace(to_replace=regex, value=regex_replace, regex=True)
    return (tmpdf)


def remove_commas(tmpdf, metadata, copy=True):
    if copy is True:
        tmpdf = tmpdf.copy()
    cols = tmpdf.columns
    for col in cols:
        tmpdf[col] = tmpdf.loc[:, col].str.replace(",", "")
    return (tmpdf)


def str_to_int(tmpdf, metadata, copy=True):
    if copy is True:
        tmpdf = tmpdf.copy()
    cols = metadata[metadata['str_to_int'].isin(['1'])]['column_name'].tolist()
    log.info("Converting string to int columns")
    for col in cols:
        tmpdf[col] = tmpdf[col].astype(int)
    return (tmpdf)


def float_to_object(tmpdf, metadata, copy=True):
    if copy is True:
        tmpdf = tmpdf.copy()
    cols = metadata[metadata['float_to_object'].isin(["1"])]['column_name'].tolist()
    for col in cols:
        log.info("Converting {0} float to object...".format(col))
        tmpdf[col] = tmpdf.loc[:,col].astype(object)
    return (tmpdf)


def object_to_int(tmpdf, metadata, copy=True):
    if copy is True:
        tmpdf = tmpdf.copy()
    cols = metadata[metadata['object_to_int'].isin(["1"])]['column_name'].tolist()
    for col in cols:
        log.info("Converting {0} object_to_int...".format(col))
        tmpdf[col] = tmpdf.loc[:,col].astype(int)
    return (tmpdf)


def object_to_float(tmpdf, metadata, copy=True):
    if copy is True:
        tmpdf = tmpdf.copy()
    cols = metadata[metadata['object_to_float'].isin(["1"])]['column_name'].tolist()
    for col in cols:
        log.info("Converting {0} object to float...".format(col))
        tmpdf[col] = tmpdf.loc[:,col].astype(float)
    return (tmpdf)


def float_to_int(tmpdf, metadata, copy=True):
    if copy is True:
        tmpdf = tmpdf.copy()
    cols = metadata[metadata['float_to_int'].isin(["1"])]['column_name'].tolist()
    for col in cols:
        log.info("Converting {0} float to int...".format(col))
        tmpdf[col] = tmpdf.loc[:,col].astype(int)
    return (tmpdf)
