"""Verify argument forwarding at the child-process boundary."""
import os
import sys
import unittest
from unittest.mock import patch

from protolab import cli


class LauncherTests(unittest.TestCase):
    def test_inference_forwards_arguments_without_adding_presets(self):
        supplied = ['--simulator', 'isaaclab', '--checkpoint', 'results/my run/last.ckpt', '--num-envs=2']
        with patch.object(sys, 'argv', ['inference', *supplied]), patch('os.execve') as execute:
            cli.inference()
        executable, command, environment = execute.call_args.args
        self.assertEqual(command, [sys.executable, '-u', '-m', 'protomotions.inference_agent', *supplied])
        self.assertEqual(executable, sys.executable)

    def test_train_preserves_arguments_and_runtime_environment(self):
        supplied = ['--experiment-path', 'experiments/custom.py', '--training-max-iterations', '2']
        with patch.object(sys, 'argv', ['train', *supplied]), patch.dict(os.environ, {'PYTHONPATH': '/ambient', 'TORCH_COMPILE_DISABLE': '0'}), patch('os.execve') as execute:
            cli.train()
        _, command, environment = execute.call_args.args
        self.assertEqual(command, [sys.executable, '-u', '-m', 'protomotions.train_agent', *supplied])
        self.assertNotIn('PYTHONPATH', environment)
        self.assertEqual(environment['TORCH_COMPILE_DISABLE'], '0')


if __name__ == '__main__':
    unittest.main()
