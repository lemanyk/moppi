"""
Modern Python Package Installer
"""

import io
import json
import sys
import urllib.request
from zipfile import ZipFile

import yaml


def get(package: str, packages: dict, needed_by: None | list, is_dev: bool):
    """PART 1: get the file"""
    url = f'https://pypi.org/pypi/{package}/json'

    data = urllib.request.urlopen(url).read()
    info = json.loads(data)

    package = info['info']['name']
    version = info['info']['version']
    package_url = info['urls'][0]['url']
    filename = info['urls'][0]['filename']

    if package in packages['all']:
        print(f'Package {package}=={version} is already installed')
        return

    print('Downloading', filename)

    data = urllib.request.urlopen(package_url).read()
    #open(filename, 'wb').write(data)

    file = ZipFile(io.BytesIO(data))
    file.extractall(sys.path[-1])

    package_info = {
        'name': package,
        'sha256': info['urls'][0]['digests']['sha256'],
        'version': version,
    }

    if needed_by:
        package_info['needed_by'] = [needed_by]
        packages['indirect_dependencies'][package] = package_info
    elif is_dev:
        packages['dev_dependencies'][package] = package_info
    else:
        packages['dependencies'][package] = package_info

    packages['all'].add(package)

    if info['info']['requires_dist']:
        for dependecy in info['info']['requires_dist']:
            if ' ' in dependecy:
                dep_package, versions = dependecy.split(' ', 1)
            else:
                dep_package, versions = dependecy, ''
            print('Versions', versions)

            if 'Windows' in versions:
                continue

            if dep_package not in packages['all']:
                get(dep_package, packages, package, is_dev)


def install(package: str, is_dev: bool = False):
    """Install a package"""
    config = load_config()
    print(config)
    packages = {
        'dependencies': {},
        'dev_dependencies': {},
        'indirect_dependencies': {},
        'all': set(),
    }
    packages.update(config)
    packages['all'] = (set(packages['dependencies'].keys()) | set(packages['dev_dependencies'].keys())
                       | set(packages['indirect_dependencies'].keys()))
    print('Installed packages', packages)

    get(package, packages, None, is_dev)
    del packages['all']

    with open('moppi.yaml', 'w', encoding='utf8') as yaml_file:
        yaml.dump(packages, yaml_file)


def load_config():
    """Loads moppi.yaml file"""
    try:
        with open('moppi.yaml', 'r', encoding='utf8') as yaml_file:
            return yaml.load(yaml_file, yaml.Loader)
    except FileNotFoundError:
        return {}


install('Werkzeug')
