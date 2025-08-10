"""Script para reubicar tests de unidad según la nueva convención.

Operaciones:
- tests/unit/test_correo_tareas_manager.py -> tests/unit/correo_tareas/test_correo_tareas_manager.py
- tests/unit/test_html_report_generator_moderno.py -> tests/unit/common/test_html_report_generator.py (rename)
- tests/common/test_config.py -> tests/unit/common/test_config.py
- tests/common/test_utils_tasks.py -> tests/unit/common/test_utils_tasks.py

También ajusta imports y lógica de localización de src en cada archivo movido.
El script es idempotente (ignora movimientos ya realizados).
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / 'tests'

moves = [
    (
        TESTS / 'unit' / 'test_correo_tareas_manager.py',
        TESTS / 'unit' / 'correo_tareas' / 'test_correo_tareas_manager.py'
    ),
    (
        TESTS / 'unit' / 'test_html_report_generator_moderno.py',
        TESTS / 'unit' / 'common' / 'test_html_report_generator.py'
    ),
    (
        TESTS / 'common' / 'test_config.py',
        TESTS / 'unit' / 'common' / 'test_config.py'
    ),
    (
        TESTS / 'common' / 'test_utils_tasks.py',
        TESTS / 'unit' / 'common' / 'test_utils_tasks.py'
    ),
]

for src, dst in moves:
    if not src.exists():
        # Ya movido o inexistente
        continue
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        if dst.exists():
            # Si ya existe con el nombre destino, asumimos que el movimiento previo se realizó
            # y continuamos (opcionalmente podríamos comparar contenidos)
            print(f"Destino ya existe, se omite: {dst.relative_to(ROOT)}")
            continue
        src.rename(dst)
        print(f"Movido {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
    except Exception as exc:
        print(f"No se pudo mover {src} -> {dst}: {exc}")

# Parches de contenido

def ensure_src_insertion(lines: list[str]) -> list[str]:
    """Reemplaza bloques ad-hoc de manipulación sys.path por una rutina robusta."""
    out: list[str] = []
    replaced = False
    skip_next = False
    for i, line in enumerate(lines):
        if 'sys.path.insert' in line or 'parent.parent.parent' in line or 'project_root' in line and 'src' in line:
            # Saltar este y quizá algunas líneas relacionadas - simplificamos detectando hasta 6 líneas siguientes si contienen 'src'
            replaced = True
            continue
        out.append(line)
    if replaced:
        bootstrap = [
            "from pathlib import Path",
            "import sys",
            "def _add_src_to_path():",
            "    for parent in Path(__file__).resolve().parents:",
            "        candidate = parent / 'src'",
            "        if candidate.is_dir():",
            "            if str(candidate) not in sys.path:",
            "                sys.path.insert(0, str(candidate))",
            "            return",
            "_add_src_to_path()",
            ""
        ]
        # Insert bootstrap at beginning (after docstring / initial comments)
        insertion_index = 0
        if out and out[0].startswith('"""'):
            # find end of docstring
            for j in range(1, len(out)):
                if out[j].startswith('"""'):
                    insertion_index = j + 1
                    break
        out = out[:insertion_index] + bootstrap + out[insertion_index:]
    return out

# Ajustes específicos de imports

def adjust_imports(path: Path):
    txt = path.read_text(encoding='utf-8').splitlines()
    # Normalizar a usar from src.common... donde proceda
    new_lines = []
    for line in txt:
        if 'from common.html_report_generator' in line:
            line = line.replace('from common.html_report_generator', 'from src.common.html_report_generator')
        if 'from common.utils' in line:
            line = line.replace('from common.utils', 'from src.common.utils')
        new_lines.append(line)
    new_lines = ensure_src_insertion(new_lines)
    path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')

for p in [
    TESTS / 'unit' / 'correo_tareas' / 'test_correo_tareas_manager.py',
    TESTS / 'unit' / 'common' / 'test_html_report_generator.py',
    TESTS / 'unit' / 'common' / 'test_utils_tasks.py',
]:
    if p.exists():
        adjust_imports(p)

print('Reubicación y ajustes completados.')
