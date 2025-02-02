"""
Copyright (c) 2013, William Ting

*  This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3, or (at your option)
any later version.

*  This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

*  You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

  Original code: https://github.com/wting/srt-resync
      Issue: the file in the repo doesn't contain any python format, so in
      environments like Windows it can't run without modifying its extension
      to srt-resync.py

This script was copied from
https://ourcodeworld.com/articles/read/968/how-to-re-synchronize-shift-subtitles-of-a-movie-from-a-srt-file-in-python-3
"""

import argparse
import datetime
import os
import re
import shutil
import sys
from io import FileIO as file
from pathlib import Path
from typing import Generator, Any

VERSION = "0.1"


def parse_options():
    global VERSION

    parser = argparse.ArgumentParser(description="Offset srt subtitles.")

    parser.add_argument(
        "offset", type=float, help="Add this many seconds to each timestamp"
    )
    parser.add_argument("srt_file", type=file)
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s " + VERSION,
        help="show version information and quit",
    )

    return parser.parse_args()


def rzeropad(ms):
    ms = str(int(ms))
    while len(ms) < 3:
        ms += "0"
    return ms


def offset_time(offset: float, time_string: str):
    # NOTE: does not support timestamps >= 24 hours
    ts = time_string.replace(",", ":").split(":")
    ts = [int(x) for x in ts]
    # millisecond -> microsecond
    ts = datetime.datetime(2013, 1, 2, ts[0], ts[1], ts[2], ts[3] * 1000)
    yesterday = datetime.datetime(2013, 1, 1, 23, 59, 59, 9999)

    delta = datetime.timedelta(seconds=offset)
    ts += delta

    if ts < yesterday:
        raise ValueError("offset would set timestamp to negative")

    # microsecond -> millisecond
    return "%s,%s" % (ts.strftime("%H:%M:%S"), rzeropad(ts.microsecond / 1000))


def get_modified_filename(name: str) -> str:
    return os.path.splitext(name)[0] + "-resync.srt"


def resync_line(
    line: str,
    offset: int,
) -> str:
    match = re.search(r"^(\d+:\d+:\d+,\d+)\s+--\>\s+(\d+:\d+:\d+,\d+)", line)
    if match:
        start = offset_time(offset, match.group(1))
        end = offset_time(offset, match.group(2))
        return f"{start} --> {end}\n"
    else:
        return line


if __name__ == "__main__":
    options = parse_options()
    if not options.srt_file.name.endswith(".srt"):
        raise sys.exit("ERROR: file name must end in .srt")

    BATCH_SIZE = 1024
    with (
        open(options.srt_file.name, "r") as infile,
        open(get_modified_filename((options.srt_file.name)), "w") as outfile,
    ):
        batch = []
        for line in infile:
            try:
                updated_line = resync_line(line, options.offset)
            except ValueError as e:
                sys.exit(f"Error: {e}")
            batch.append(updated_line)
            if len(batch) > BATCH_SIZE:
                outfile.writelines(batch)
                batch = []
