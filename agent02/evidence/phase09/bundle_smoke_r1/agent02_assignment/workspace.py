"""Small, tested workspace guards; never import or run the teacher's program."""

import ast
import hashlib
import json
from pathlib import Path, PureWindowsPath


def inside(base: Path, relative: str) -> Path:
    """Resolve a portable relative target and reject traversal and symlink escape."""
    windows = PureWindowsPath(relative)
    if not relative or windows.drive or windows.root or '\\' in relative:
        raise ValueError('Target must be a nonempty portable relative path')
    target = (base / relative).resolve()
    if Path(relative).is_absolute() or not target.is_relative_to(base.resolve()):
        raise ValueError('Target escapes the assignment workspace')
    return target


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_verified(source: Path, base: Path, relative: str, expected: str) -> dict:
    """Copy exact bytes once; reuse identical files and refuse user-file overwrite."""
    target = inside(base, relative)
    content = source.read_bytes()
    actual = hashlib.sha256(content).hexdigest()
    if actual != expected:
        raise ValueError(f'Source hash mismatch: {source.name}')
    operation = 'reused'
    if target.exists():
        if sha256_file(target) != expected:
            raise FileExistsError(f'Refusing to overwrite different target: {target}')
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(content)
        operation = 'copied'
    return {'path': relative, 'bytes': len(content), 'sha256': actual, 'operation': operation}


def inspect_python(path: Path) -> dict:
    """Parse and compile without exec/import, preserving original newline bytes."""
    content = path.read_bytes()
    tree = ast.parse(content, filename=str(path))
    compile(tree, str(path), 'exec')
    classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    defaults = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == 'Config':
            for field in node.body:
                if isinstance(field, ast.AnnAssign) and isinstance(field.target, ast.Name):
                    defaults[field.target.id] = ast.literal_eval(field.value)
    return {'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content),
            'lines': len(content.splitlines()), 'syntax_valid': True,
            'execution_performed': False, 'classes': classes, 'functions': functions,
            'config_defaults': defaults}


def prepare_sources(source_root: Path, base: Path, manifest: list) -> dict:
    """Validate the whole manifest before writing any original-source copy."""
    if not manifest:
        raise ValueError('Source manifest is empty')
    for record in manifest:
        name = record['name']
        if Path(name).name != name or PureWindowsPath(name).name != name or name in {'.', '..'}:
            raise ValueError('Source name must be a basename')
        source = inside(source_root, name)
        if source.stat().st_size != record['bytes']:
            raise ValueError(f'Source size mismatch: {name}')
        if sha256_file(source) != record['sha256']:
            raise ValueError(f'Source hash mismatch: {name}')
    copies = [copy_verified(source_root / record['name'], base,
                            'sources/provided/' + record['name'], record['sha256'])
              for record in manifest]
    code_record = next(record for record in manifest if record['name'] == 'agent02_code.tex')
    reference = copy_verified(source_root / code_record['name'], base,
                              'code/agent02_experiment.py', code_record['sha256'])
    inspection = inspect_python(base / reference['path'])
    return {'sources': copies, 'reference': reference, 'inspection': inspection}


def validate_runtime(actual: dict, expected: dict) -> None:
    if actual['python'] != expected['python']:
        raise ValueError('Python version changed from the pinned runtime')
    for name, version in expected.get('packages', {}).items():
        if actual['packages'].get(name) != version:
            raise ValueError(f'Pinned package mismatch: {name}')


def write_receipt(base: Path, relative: str, value: dict) -> Path:
    """New generated JSON artifact, with explicit no-overwrite semantics."""
    target = inside(base, relative)
    if target.exists():
        if json.loads(target.read_text(encoding='utf-8')) != value:
            raise FileExistsError(f'Receipt already exists with different content: {target}')
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    return target
