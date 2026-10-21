import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    loader = importlib.machinery.SourceFileLoader(name.replace('-', '_'), str(ROOT / 'bin' / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class ConnectionTests(unittest.TestCase):
    def test_switch_once_then_again_on_reconnect(self):
        module = load('voyager-layer-auto')
        a, b = {('1-5', '1', '6')}, {('1-5', '1', '7')}
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'config.json'
            config.write_text('{"layer": 3}')
            with patch.object(module, 'CONFIG', config), \
                 patch.object(module, 'devices', side_effect=[a, a, set(), b, b]), \
                 patch.object(module, 'select_layer', return_value=(True, '')) as select, \
                 patch.object(module.time, 'sleep'):
                with self.assertRaises(StopIteration):
                    module.main()
                self.assertEqual(select.call_count, 2)

    def test_failed_api_call_retries_before_marking_done(self):
        module = load('voyager-layer-auto')
        a = {('1-5', '1', '6')}
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'config.json'
            config.write_text('{"layer": 3}')
            with patch.object(module, 'CONFIG', config), \
                 patch.object(module, 'devices', side_effect=[a, a, a]), \
                 patch.object(module, 'select_layer', side_effect=[(False, 'Starting'), (True, '')]) as select, \
                 patch.object(module.time, 'monotonic', side_effect=[0, 0, 3]), \
                 patch.object(module.time, 'sleep'):
                with self.assertRaises(StopIteration):
                    module.main()
                self.assertEqual(select.call_count, 2)


class LauncherTests(unittest.TestCase):
    def test_existing_hidden_window_revealed_without_launch(self):
        module = load('keymapp-show')
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {'XDG_RUNTIME_DIR': directory}), \
             patch.object(module, 'state', side_effect=[
                 [{'class': 'keymapp'}], [{'specialWorkspace': {'name': ''}}]]), \
             patch.object(module.subprocess, 'Popen') as launch, \
             patch.object(module.subprocess, 'run') as run:
            module.main()
            launch.assert_not_called()
            self.assertIn('toggle_special', run.call_args.args[0][-1])

    def test_visible_window_stays_visible(self):
        module = load('keymapp-show')
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {'XDG_RUNTIME_DIR': directory}), \
             patch.object(module, 'state', side_effect=[
                 [{'class': 'keymapp'}], [{'specialWorkspace': {'name': 'special:keymapp'}}]]), \
             patch.object(module.subprocess, 'Popen') as launch, \
             patch.object(module.subprocess, 'run') as run:
            module.main()
            launch.assert_not_called()
            run.assert_not_called()


class InstallerTests(unittest.TestCase):
    def test_install_update_uninstall_preserves_user_files(self):
        with tempfile.TemporaryDirectory(prefix='voyager test ') as directory:
            home = Path(directory)
            config = home / '.config'
            hypr = config / 'hypr/hyprland.lua'
            hypr.parent.mkdir(parents=True)
            hypr.write_text('-- existing config\n')
            desktop = home / '.local/share/applications/keymapp.desktop'
            desktop.parent.mkdir(parents=True)
            desktop.write_text('original launcher\n')
            env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(config),
                       XDG_DATA_HOME=str(home / '.local/share'))
            # Keep test prerequisites separate from installed output files.
            fake_bin = home / 'prerequisites'
            fake_bin.mkdir()
            for name in ('kontroll', 'keymapp', 'hyprctl'):
                path = fake_bin / name
                path.write_text('#!/bin/sh\nexit 0\n')
                path.chmod(0o755)
            env['PATH'] = str(fake_bin) + os.pathsep + env['PATH']
            def install(*args):
                subprocess.run(['python3', str(ROOT / 'install'), '--no-start', *args],
                               env=env, check=True, capture_output=True)
            install('--layer', '3')
            install('--layer', '4')
            self.assertEqual(hypr.read_text().count('-- BEGIN voyager-layer-auto'), 1)
            self.assertEqual(json.loads((config / 'voyager-layer/config.json').read_text())['layer'], 4)
            self.assertIn(str(home), desktop.read_text())
            install('--uninstall')
            self.assertEqual(hypr.read_text().strip(), '-- existing config')
            self.assertEqual(desktop.read_text(), 'original launcher\n')
            self.assertFalse((home / '.local/bin/keymapp-show').exists())
            self.assertTrue((config / 'voyager-layer/config.json').exists())


if __name__ == '__main__':
    unittest.main()
