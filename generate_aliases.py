#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
import itertools
import os.path
import sys

try:
    xrange  # Python 2
except NameError:
    xrange = range  # Python 3


def main():
    # (alias, full, allow_when_oneof, incompatible_with)
    cmds = [('k', 'kubectl', None, None)]

    globs = []

    ops = [
        ('a', 'apply', None, None),
        ('k', 'kustomize', None, None),
        ('ex', 'exec', None, None),
        ('lo', 'logs', None, None),
        ('g', 'get', None, None),
        ('d', 'describe', None, None),
        ('del', 'delete', None, None),
        ('c', 'create', None, None),
        ('run', 'run', None, None),
    ]

    res = [
        ('po', 'pods', ['g', 'd', 'del'], None),
        ('dep', 'deployment', ['g', 'd', 'del', 'c'], None),
        ('ds', 'daemonset', ['g', 'd', 'del'], None),
        ('svc', 'service', ['g', 'd', 'del'], None),
        ('ing', 'ingress', ['g', 'd', 'del'], None),
        ('cm', 'configmap', ['g', 'd', 'del', 'c'], None),
        ('sec', 'secret', ['g', 'd', 'del', 'c'], None),
        ('no', 'nodes', ['g', 'd'], None),
        ('ns', 'namespaces', ['g', 'd', 'del', 'c'], None),
        ('sa', 'serviceaccounts', ['g', 'd', 'del', 'c'], None),
    ]
    res_types = [r[0] for r in res]

    args = [
        ('oyaml', '-o=yaml', ['g', 'c'], ['owide', 'ojson', 'sl']),
        ('owide', '-o=wide', ['g'], ['oyaml', 'ojson']),
        ('ojson', '-o=json', ['g'], ['owide', 'oyaml', 'sl']),
        ('all', '--all-namespaces', ['g', 'd'], ['del', 'f', 'no']),
        ('sl', '--show-labels', ['g'], ['oyaml', 'ojson'], None),
        ('w', '--watch', ['g'], ['oyaml', 'ojson', 'owide']),
        ('drc', '--dry-run=client', ['a', 'c', 'run'], ['owide', 'all', 'sl', 'w', 'drs']),
        ('drs', '--dry-run=server', ['a', 'c', 'run'], ['owide', 'all', 'sl', 'w', 'drc']),
    ]

    # these accept a value, so they need to be at the end and
    # mutually exclusive within each other.
    positional_args = [
        ('f', '-f', ['g', 'd', 'del', 'c'],
        res_types + ['all', 'l']),
        ('l', '-l', ['g', 'd', 'del'], ['f', 'all']),
        ('n', '--namespace', ['g', 'd', 'del', 'lo', 'ex', 'pf'], ['ns', 'no', 'all'])
    ]

    # [(part, optional, take_exactly_one)]
    parts = [
        (cmds, False, True),
        (globs, True, False),
        (ops, True, True),
        (res, True, True),
        (args, True, False),
        (positional_args, True, True),
        ]

    shellFormatting = {
        "bash": "alias {}='{}'",
        "zsh": "alias {}='{}'",
        "fish": "abbr --add {} \"{}\"",
    }

    shell = sys.argv[1] if len(sys.argv) > 1 else "bash"
    if shell not in shellFormatting:
        raise ValueError("Shell \"{}\" not supported. Options are {}"
                        .format(shell, [key for key in shellFormatting]))

    out = gen(parts)

    # prepare output
    if not sys.stdout.isatty():
        header_path = \
            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'license_header')
        with open(header_path, 'r') as f:
            print(f.read())

    seen_aliases = set()

    for cmd in out:
        alias = ''.join([a[0] for a in cmd])
        command = ' '.join([a[1] for a in cmd])

        if alias in seen_aliases:
            print("Alias conflict detected: {}".format(alias), file=sys.stderr)

        seen_aliases.add(alias)

        print(shellFormatting[shell].format(alias, command))


def gen(parts):
    out = [()]
    for (items, optional, take_exactly_one) in parts:
        orig = list(out)
        combos = []

        if optional and take_exactly_one:
            combos = combos.append([])

        if take_exactly_one:
            combos = combinations(items, 1, include_0=optional)
        else:
            combos = combinations(items, len(items), include_0=optional)

        # permutate the combinations if optional (args are not positional)
        if optional:
            new_combos = []
            for c in combos:
                new_combos += list(itertools.permutations(c))
            combos = new_combos

        new_out = []
        for segment in combos:
            for stuff in orig:
                if is_valid(stuff + segment):
                    new_out.append(stuff + segment)
        out = new_out
    return out


def is_valid(cmd):
    return is_valid_requirements(cmd) and is_valid_incompatibilities(cmd)


def is_valid_requirements(cmd):
    parts = {c[0] for c in cmd}

    for i in range(0, len(cmd)):
        # check at least one of requirements are in the cmd
        requirements = cmd[i][2]
        if requirements and len(parts & set(requirements)) == 0:
            return False

    return True


def is_valid_incompatibilities(cmd):
    parts = {c[0] for c in cmd}

    for i in range(0, len(cmd)):
        # check none of the incompatibilities are in the cmd
        incompatibilities = cmd[i][3]
        if incompatibilities and len(parts & set(incompatibilities)) > 0:
            return False

    return True


def combinations(a, n, include_0=True):
    l = []
    for j in xrange(0, n + 1):
        if not include_0 and j == 0:
            continue

        cs = itertools.combinations(a, j)

        # check incompatibilities early
        cs = (c for c in cs if is_valid_incompatibilities(c))

        l += list(cs)

    return l


def diff(a, b):
    return list(set(a) - set(b))


if __name__ == '__main__':
    main()
