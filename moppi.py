"""
Modern Python Package Installer
"""

import io
import json
import urllib.request
from zipfile import ZipFile


def get(package):
    """PART 1: get the file"""
    url = f'https://pypi.org/pypi/{package}/json'

    data = urllib.request.urlopen(url).read()
    info = json.loads(data)

    package_url = info['urls'][0]['url']
    filename = info['urls'][0]['filename']
    print("Downloading", filename)

    data = urllib.request.urlopen(package_url).read()
    #open(filename, 'wb').write(data)

    file = ZipFile(io.BytesIO(data))
    file.extractall('libs')


get('flask')
