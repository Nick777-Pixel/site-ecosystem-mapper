"""Utils."""

from collections import namedtuple
from datetime import datetime, timedelta
from typing import Optional
from base64 import b64encode

import numpy as np
import pandas as pd


def build_download_link(st, filename: str, df: pd.DataFrame):
    phrase = "Download "

    csv = dataframe_to_base64(df)
    st.markdown("""
        <a download="{filename}" href="data:file/csv;base64,{csv}">{phrase} CSV</a>
""".format(csv=csv,filename=filename,phrase=phrase), unsafe_allow_html=True)


def dataframe_to_base64(df: pd.DataFrame) -> str:
    """Converts a dataframe to a base64-encoded CSV representation of that data.
    This is useful for building datauris for use to download the data in the browser.
    Arguments:
        df: The dataframe to convert
    """
    csv = df.to_csv(index=False)
    b64 = b64encode(csv.encode()).decode()
    return b64
