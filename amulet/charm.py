import os
import yaml
import shutil
import tempfile

from charmworldlib.charm import Charm
from .helpers import run_bzr, setup_bzr


def get_relation(charm, relation, cache=None):
    if cache and charm in cache:
        c = cache[charm]
    else:
        c = get_charm(charm)

    relations = c.relations

    if not relations:
        raise Exception('No relations for charm')

    for rel_type in relations:
        for rel_name in relations[rel_type]:
            if rel_name == relation:
                return rel_type, relations[rel_type][rel_name]['interface']

    return (None, None)


def get_charm(charm_path):
    if charm_path.startswith('cs:'):
        return Charm(charm_path)
    if charm_path.startswith('lp:'):
        return LaunchpadCharm(charm_path)
    if charm_path.startswith('local:'):
        return LocalCharm(
            os.path.join(
                os.environ.get('JUJU_REPOSITORY', ''),
                charm_path[len('local:'):]))
    if os.path.exists(os.path.expanduser(charm_path)):
        return LocalCharm(charm_path)

    return Charm(charm_path)


class LocalCharm(object):
    def __init__(self, path):
        path = os.path.abspath(os.path.expanduser(path))

        if not os.path.exists(os.path.join(path, 'metadata.yaml')):
            raise Exception('Charm not found')

        if not os.path.exists(os.path.join(path, '.bzr')):
            path = self._make_temp_copy(path)

        self.url = None
        self.subordinate = False
        self.relations = {}
        self.provides = {}
        self.requires = {}
        self.code_source = self.source = {'location': path}
        self._raw = self._load(os.path.join(path, 'metadata.yaml'))
        self._parse(self._raw)

    def _make_temp_copy(self, path):
        d = tempfile.mkdtemp(prefix='charm')
        temp_charm_dir = os.path.join(d, os.path.basename(path))
        shutil.copytree(path, temp_charm_dir, symlinks=True)
        setup_bzr(temp_charm_dir)
        run_bzr(["add", "."], temp_charm_dir)
        run_bzr(["commit", "--unchanged", "-m", "Copied from {}".format(path)],
                temp_charm_dir)
        self.temp_dir = d
        return temp_charm_dir

    def _parse(self, metadata):
        rel_keys = ['provides', 'requires']
        for key, val in metadata.items():
            if key in rel_keys:
                self.relations[key] = val

            setattr(self, key, val)

    def _load(self, metadata_path):
        with open(metadata_path) as f:
            data = yaml.safe_load(f.read())

        return data

    def __str__(self):
        return yaml.dump(self._raw)

    def __repr__(self):
        return '<LocalCharm %s>' % self.code_source['location']

    def __del__(self):
        temp_dir = getattr(self, 'temp_dir', None)
        if temp_dir:
            shutil.rmtree(temp_dir)


class LaunchpadCharm(object):
    def __init__(self, branch):
        self.url = None
        self.subordinate = False
        self.code_source = self.source = {'location': branch, 'type': 'bzr'}
        self.relations = {}
        self.provides = {}
        self.requires = {}
        self._raw = self._load(os.path.join(branch, 'metadata.yaml'))
        self._parse(self._raw)

    def _parse(self, metadata):
        rel_keys = ['provides', 'requires']
        for key, val in metadata.items():
            if key in rel_keys:
                self.relations[key] = val

            setattr(self, key, val)

    def _load(self, metadata_path):
        mdata = run_bzr(['cat', metadata_path], None)
        return yaml.safe_load(mdata)

    def __str__(self):
        return yaml.dump(self._raw)

    def __repr__(self):
        return '<LaunchpadCharm %s>' % self.code_source['location']
