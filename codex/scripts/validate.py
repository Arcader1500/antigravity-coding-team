"""Validate Codex source configuration, optionally comparing installed files."""
import argparse
import json
from pathlib import Path
import sys

if sys.version_info < (3, 11):
    raise SystemExit('Codex source validation and risk logging require Python 3.11 or newer.')

import tomllib

SOURCE_MODELS = {
    'planner': ('gpt-6-luna', 'high'),
    'plan-critic': ('gpt-6.1-sol', 'medium'),
    'researcher': ('gpt-6-luna', 'low'),
    'orchestrator': ('gpt-6.1-sol', 'low'),
    'implementer': ('gpt-6-luna', 'medium'),
    'code-reviewer': ('gpt-6.1-sol', 'medium'),
    'verifier': ('gpt-6-luna', 'low'),
    'devops-expert': ('gpt-6-luna', 'medium'),
    'risk-estimator': ('gpt-6.1-sol', 'medium'),
}
PROFILE_MODELS = {
    'planner': ('gpt-6.1-sol', 'medium'),
    'orchestrator': ('gpt-6.1-sol', 'low'),
}


def _read_agent(path: Path, name: str) -> dict:
    agent = tomllib.loads(path.read_text(encoding='utf-8-sig'))
    if agent.get('name') != name:
        raise ValueError(f'{path}: expected agent name {name}')
    if (agent.get('model'), agent.get('model_reasoning_effort')) != SOURCE_MODELS[name]:
        raise ValueError(f'{path}: source model/effort does not match {SOURCE_MODELS[name]}')
    if not agent.get('developer_instructions', '').strip():
        raise ValueError(f'{path}: developer instructions are empty')
    return agent


def validate_source(root: Path) -> None:
    agents_dir = root / 'agents'
    if {path.stem for path in agents_dir.glob('*.toml')} != set(SOURCE_MODELS):
        raise ValueError('source agent definitions do not match the nine expected roles')
    for name in SOURCE_MODELS:
        _read_agent(agents_dir / f'{name}.toml', name)

    manifest = json.loads((root / '.codex-plugin/plugin.json').read_text(encoding='utf-8-sig'))
    if manifest.get('skills') != './skills/':
        raise ValueError('Codex plugin manifest must package ./skills/')
    skills = list((root / 'skills').glob('*/SKILL.md'))
    if len(skills) != 12:
        raise ValueError(f'expected twelve skills; found {len(skills)}')
    for entry, role in {'team-plan': 'planner', 'team-run': 'orchestrator'}.items():
        path = root / f'skills/{entry}/SKILL.md'
        text = path.read_text(encoding='utf-8')
        if not (path.parent / f'../../agents/{role}.toml').resolve().is_file() or f'../../agents/{role}.toml' not in text:
            raise ValueError(f'{path}: missing linked {role} role')
    if 'agent_type="code-reviewer"' not in (root / 'skills/team-review/SKILL.md').read_text(encoding='utf-8'):
        raise ValueError('team-review must dispatch code-reviewer')
    for path in skills:
        text = path.read_text(encoding='utf-8-sig')
        if not text.startswith('---\n') or '\nname:' not in text or '\ndescription:' not in text or 'superpowers:' in text:
            raise ValueError(f'{path}: malformed or unsupported skill frontmatter')

    risk_helper = root / 'scripts/risk_store.py'
    if not risk_helper.is_file():
        raise ValueError(f'missing packaged risk-store helper: {risk_helper}')
    antigravity_helper = root.parent / 'antigravity/scripts/risk_store.py'
    if not antigravity_helper.is_file() or risk_helper.read_bytes() != antigravity_helper.read_bytes():
        raise ValueError('Codex and Antigravity risk-store helpers must be byte-identical')
    codex_installer = (root / 'install.ps1').read_text(encoding='utf-8')
    if 'Copy-Item "$PSScriptRoot\\*" $pluginTarget -Recurse -Force' not in codex_installer:
        raise ValueError('Codex installer must include packaged scripts in the plugin copy')
    antigravity_installer = (root.parent / 'antigravity/install.ps1').read_text(encoding='utf-8')
    if '& $AgyPath plugin install "$PluginDir"' not in antigravity_installer:
        raise ValueError('Antigravity installer must install the complete plugin directory')
    antigravity_text = (root.parent / 'antigravity/agents/risk-estimator.md').read_text(encoding='utf-8')
    parts = antigravity_text.split('---', 2)
    if len(parts) != 3:
        raise ValueError('Antigravity risk-estimator frontmatter is malformed')
    antigravity_body = parts[2].strip()
    codex_body = tomllib.loads((agents_dir / 'risk-estimator.toml').read_text(encoding='utf-8'))['developer_instructions'].strip()
    if antigravity_body != codex_body:
        raise ValueError('risk-estimator instruction bodies differ between Codex and Antigravity')


def validate_installed(root: Path, home: Path) -> None:
    agents = root / 'agents'
    for name in SOURCE_MODELS:
        source = agents / f'{name}.toml'
        installed = home / 'agents' / source.name
        if not installed.is_file() or installed.read_bytes() != source.read_bytes():
            raise ValueError(f'installed agent differs from source or is missing: {installed}')

    for name, settings in PROFILE_MODELS.items():
        path = home / f'coding-team-{name}.config.toml'
        profile = tomllib.loads(path.read_text(encoding='utf-8-sig'))
        if (profile.get('model'), profile.get('model_reasoning_effort')) != settings:
            raise ValueError(f'{path}: launch-profile model/effort does not match {settings}')
        role = _read_agent(agents / f'{name}.toml', name)
        if profile.get('developer_instructions', '').strip() != role['developer_instructions'].strip():
            raise ValueError(f'{path}: launch-profile instructions differ from source role')

    cache = home / 'plugins/cache/coding-team-local/coding-team/1.0.0'
    for path in root.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            installed = cache / path.relative_to(root)
            if not installed.is_file() or installed.read_bytes() != path.read_bytes():
                raise ValueError(f'installed plugin cache differs from source or is missing: {installed}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--source-only', action='store_true', help='validate repository sources without reading user install state (default)')
    modes.add_argument('--installed-parity', action='store_true', help='also compare installed agents, launch profiles and plugin cache')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    try:
        validate_source(root)
        print('PASS: source-only validation (9 role models, 12 skills, packaged helper parity and links).')
        if args.installed_parity:
            validate_installed(root, Path.home() / '.codex')
            print('PASS: installed agent, launch-profile and plugin-cache parity.')
        else:
            print('NOTE: installed parity was not checked; use --installed-parity after installation.')
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f'FAIL: {str(exc)[:300]}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
