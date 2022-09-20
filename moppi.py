"""
Modern Python Package Installer
"""

import argparse
from importlib.resources import Package
import io
import json
import sys
import urllib.request
from zipfile import ZipFile

import yaml


class Moppi:

    def __init__(self, config_file: str = 'moppi.yaml') -> None:
        self.config_file = config_file
        self.dependencies = {}
        self.dev_dependencies = {}
        self.indirect_dependencies = {}

    def run(self) -> None:
        """Execute install, remove, update or apply"""
        command, package = self._parse_args()
        match command:
            case 'install':
                print(f'Installing {package}')
                self.install(package)
            case 'remove':
                print(f'Removing {package}')
                self.remove(package)

    def _parse_args(self) -> tuple[str]:
        """Parse the command line args"""
        CHOICES = ('install', 'remove', 'update')
        parser = argparse.ArgumentParser('Moppi package installer')
        parser.add_argument('command', type=str, choices=CHOICES, help='command to execute')
        parser.add_argument('package', type=str, help='package name')
        args = parser.parse_args()
        command = args.command
        package = args.package
        return command, package

    def _load_config(self) -> dict:
        """Loads moppi.yaml file"""
        try:
            with open(self.config_file, 'r', encoding='utf8') as yaml_file:
                config = yaml.load(yaml_file, yaml.Loader)
        except FileNotFoundError:
            config = {}
        print('Current config', config)

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

        return packages

    def _save_config(self, packages: dict):
        """Save the config into moppi.yaml file"""
        del packages['all']
        with open('moppi.yaml', 'w', encoding='utf8') as yaml_file:
            yaml.dump(packages, yaml_file)

    def install(self, package: str, is_dev: bool = False) -> None:
        """Install a package"""
        packages = self._load_config()

        self._get(package, packages, None, is_dev)
        self._save_config(packages)

    def _get(self, package: str, packages: dict, needed_by: None | list, is_dev: bool) -> None:
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
                    self._get(dep_package, packages, package, is_dev)

    def remove(self, package: str):
        """Remove a package"""

    def update(self, package):
        """Update a package"""

    def apply(self):
        """Apply the moppi.yaml config"""


if __name__ == '__main__':
    #Moppi().install('Werkzeug')
    Moppi().run()
