import argparse
import csv
import gzip
import hashlib
import json
import urllib.request
import zipfile

from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from ziplus import STATES_LIST

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
GEONAMES_URL = 'https://download.geonames.org/export/zip/US.zip'


def get_state_index(abbv: str) -> int:
    try:
        return STATES_LIST.index(abbv.upper())
    except ValueError:
        return -1


def download() -> None:
    with NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp_path = Path(tmp.name)
    urllib.request.urlretrieve(GEONAMES_URL, tmp_path)  # noqa: S310
    with zipfile.ZipFile(tmp_path) as zf:
        zf.extract('US.txt', DATA_DIR)
        zf.extract('readme.txt', DATA_DIR)
    tmp_path.unlink()


def build_geonames() -> dict:
    with (DATA_DIR / 'US.txt').open() as tsv:
        return {
            'version': (DATA_DIR / 'version.txt').read_text().strip(),
            'type': 'state_only',
            'zipcodes': {record[1]: idx for record in csv.reader(tsv, delimiter='\t') if (idx := get_state_index(record[4])) >= 0},
        }


def pack(zip_dict: dict) -> None:
    with gzip.open(BASE_DIR / 'ziplus' / 'zipcodes.json.gz', 'wb') as pkg:
        pkg.write(json.dumps(zip_dict).encode(encoding='ascii'))


def update_version() -> None:
    today = datetime.now(tz=UTC).date().isoformat()
    (DATA_DIR / 'version.txt').write_text(f'GeoNames US ({today}) [{GEONAMES_URL}]\n')


def main() -> None:
    parser = argparse.ArgumentParser(description='Build ziplus ZIP code dataset')
    parser.add_argument('--download', action='store_true', help='Download latest dataset from GeoNames')
    parser.add_argument('--checksum', action='store_true', help='Print SHA256 of current US.txt and exit')
    args = parser.parse_args()

    if args.checksum:
        h = hashlib.sha256((DATA_DIR / 'US.txt').read_bytes()).hexdigest()
        print(h)  # noqa: T201
        return

    if args.download:
        download()
        update_version()

    pack(build_geonames())


if __name__ == '__main__':
    main()
