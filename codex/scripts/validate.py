"""Validate generated/installed configuration without making model requests."""
import json
from pathlib import Path
import tomllib

root = Path(__file__).resolve().parent.parent
home = Path.home() / '.codex'
expected = {
    'planner': ('gpt-6-sol', 'high'),
    'plan-critic': ('gpt-6-sol', 'high'),
    'researcher': ('gpt-6-luna', 'low'),
    'orchestrator': ('gpt-6-sol', 'low'),
    'implementer': ('gpt-6-sol', 'medium'),
    'code-reviewer': ('gpt-6-sol', 'high'),
    'verifier': ('gpt-6-luna', 'low'),
}
cache = home / 'plugins/cache/coding-team-local/coding-team/1.0.0'
for name, settings in expected.items():
    source = root / f'agents/{name}.toml'
    for path in (source, home / f'agents/{name}.toml'):
        agent = tomllib.loads(path.read_text(encoding='utf-8-sig'))
        assert agent['name'] == name, path
        assert (agent['model'], agent['model_reasoning_effort']) == settings, path
        assert agent['developer_instructions'].strip(), path
        assert path.read_bytes() == source.read_bytes(), path
for name in ('planner', 'orchestrator'):
    profile = tomllib.loads((home / f'coding-team-{name}.config.toml').read_text(encoding='utf-8-sig'))
    assert (profile['model'], profile['model_reasoning_effort']) == expected[name]
    assert profile['developer_instructions'].strip()
    role = tomllib.loads((root / f'agents/{name}.toml').read_text(encoding='utf-8'))
    assert profile['developer_instructions'].strip() == role['developer_instructions'].strip(), name
manifest = json.loads((root / '.codex-plugin/plugin.json').read_text(encoding='utf-8-sig'))
assert manifest['skills'] == './skills/'
for path in (root).rglob('*'):
    if path.is_file():
        installed = cache / path.relative_to(root)
        assert installed.is_file() and installed.read_bytes() == path.read_bytes(), installed
skills = list((root / 'skills').glob('*/SKILL.md'))
assert len(skills) == 12
for entry, role in {'team-plan': 'planner', 'team-run': 'orchestrator'}.items():
    path = root / f'skills/{entry}/SKILL.md'
    assert (path.parent / f'../../agents/{role}.toml').resolve().is_file(), path
    assert f'../../agents/{role}.toml' in path.read_text(encoding='utf-8'), path
assert 'agent_type="code-reviewer"' in (root / 'skills/team-review/SKILL.md').read_text(encoding='utf-8')
for path in skills:
    text = path.read_text(encoding='utf-8-sig')
    assert text.startswith('---\n') and '\nname:' in text and '\ndescription:' in text, path
    assert 'superpowers:' not in text, path
print('PASS: 7 role mappings, 14 matching agent files, 2 profiles, 12 skills, entry-point links, installed cache parity.')
