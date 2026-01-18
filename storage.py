import json
import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict

# =========================
# Data path (SIEMPRE escribible)
# =========================
APP_NAME = "N-Notas"

def app_data_dir() -> Path:
    # Windows: %LOCALAPPDATA%\N-Notas
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
    p = Path(base) / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p

DATA_PATH = app_data_dir() / "data.json"

RAMOS_DEFAULT = ["Matemática", "Lenguaje", "Historia", "Ciencias", "Inglés"]
NIVELES = ["Escolar", "Universidad", "Postgrado"]
NIVEL_DEFAULT = "Escolar"
TOL_PESOS = 0.5  # 99.5–100.5

# =========================
# Base v1.2
# =========================
def default_data_v12() -> dict:
    return {
        "version": "1.2",
        "perfil": {"nombre": "Principal", "nivel": NIVEL_DEFAULT},
        "ramos": {r: {"evaluaciones": []} for r in RAMOS_DEFAULT},
        "ramo_activo": "Matemática",
    }

def _safe_write(data: dict) -> None:
    tmp = DATA_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(DATA_PATH)

def _is_v11(data: dict) -> bool:
    return isinstance(data, dict) and data.get("version") == "1.1" and isinstance(data.get("notas"), list)

def parse_nota(texto: str) -> Optional[float]:
    t = (texto or "").strip().replace(",", ".")
    if not t:
        return None
    try:
        n = float(t)
    except ValueError:
        return None
    if n < 1.0 or n > 7.0:
        return None
    return n

def parse_peso(texto: str) -> Optional[float]:
    t = (texto or "").strip().replace(",", ".")
    if not t:
        return None
    try:
        p = float(t)
    except ValueError:
        return None
    if not (0.0 < p <= 100.0):
        return None
    return p

def _migrate_v11_to_v12(data_v11: dict) -> dict:
    base = default_data_v12()
    evs = []
    for x in data_v11.get("notas", []):
        n = parse_nota(str(x))
        if n is not None:
            evs.append({"nota": n})
    base["ramos"]["Matemática"]["evaluaciones"] = evs
    base["ramo_activo"] = "Matemática"
    return base

def _normalize_v12(data: dict) -> Tuple[dict, bool]:
    """Retorna (data_normalizada, changed)."""
    changed = False

    if not isinstance(data, dict):
        return default_data_v12(), True

    if data.get("version") != "1.2":
        return default_data_v12(), True

    if not isinstance(data.get("perfil"), dict):
        data["perfil"] = {"nombre": "Principal", "nivel": NIVEL_DEFAULT}
        changed = True

    if not isinstance(data["perfil"].get("nombre"), str):
        data["perfil"]["nombre"] = "Principal"
        changed = True

    if data["perfil"].get("nivel") not in NIVELES:
        data["perfil"]["nivel"] = NIVEL_DEFAULT
        changed = True

    if not isinstance(data.get("ramos"), dict):
        data["ramos"] = {r: {"evaluaciones": []} for r in RAMOS_DEFAULT}
        changed = True

    # asegurar ramos default
    for r in RAMOS_DEFAULT:
        if r not in data["ramos"] or not isinstance(data["ramos"].get(r), dict):
            data["ramos"][r] = {"evaluaciones": []}
            changed = True
        if "evaluaciones" not in data["ramos"][r] or not isinstance(data["ramos"][r]["evaluaciones"], list):
            data["ramos"][r]["evaluaciones"] = []
            changed = True

    # limpiar evaluaciones
    for r, obj in list(data["ramos"].items()):
        if not isinstance(r, str) or not isinstance(obj, dict):
            try:
                del data["ramos"][r]
            except Exception:
                pass
            changed = True
            continue

        evs = obj.get("evaluaciones", [])
        if not isinstance(evs, list):
            obj["evaluaciones"] = []
            changed = True
            continue

        clean = []
        for ev in evs:
            if not isinstance(ev, dict) or "nota" not in ev:
                changed = True
                continue
            try:
                nota = float(ev["nota"])
            except Exception:
                changed = True
                continue
            if not (1.0 <= nota <= 7.0):
                changed = True
                continue

            item = {"nota": nota}
            if "peso" in ev and ev["peso"] is not None:
                try:
                    peso = float(ev["peso"])
                    if 0.0 < peso <= 100.0:
                        item["peso"] = peso
                    else:
                        changed = True
                except Exception:
                    changed = True

            clean.append(item)

        if clean != evs:
            obj["evaluaciones"] = clean
            changed = True

    # ramo activo válido
    if data.get("ramo_activo") not in data["ramos"]:
        keys = list(data["ramos"].keys())
        data["ramo_activo"] = keys[0] if keys else "Matemática"
        changed = True

    return data, changed

def load_data() -> dict:
    if not DATA_PATH.exists():
        data = default_data_v12()
        _safe_write(data)
        return data

    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except Exception:
        data = default_data_v12()
        _safe_write(data)
        return data

    if _is_v11(data):
        data = _migrate_v11_to_v12(data)
        _safe_write(data)
        return data

    data, changed = _normalize_v12(data)
    if changed:
        _safe_write(data)
    return data

def save_data(data: dict) -> None:
    data, _ = _normalize_v12(data)
    _safe_write(data)

# =========================
# Perfil / Nivel
# =========================
def get_nivel() -> str:
    return load_data().get("perfil", {}).get("nivel", NIVEL_DEFAULT)

def set_nivel(nivel: str) -> None:
    if nivel not in NIVELES:
        return
    data = load_data()
    data["perfil"]["nivel"] = nivel
    save_data(data)

def ponderacion_habilitada() -> bool:
    return get_nivel() in ("Universidad", "Postgrado")

# =========================
# Ramos CRUD
# =========================
def get_ramos() -> List[str]:
    r = load_data().get("ramos", {})
    return list(r.keys()) if isinstance(r, dict) else []

def get_ramo_activo() -> str:
    return load_data().get("ramo_activo", "Matemática")

def set_ramo_activo(ramo: str) -> None:
    data = load_data()
    if ramo in data.get("ramos", {}):
        data["ramo_activo"] = ramo
        save_data(data)

def add_ramo(nombre: str) -> Tuple[bool, str]:
    name = (nombre or "").strip()
    if not name:
        return False, "Nombre vacío."
    data = load_data()
    if name in data["ramos"]:
        return False, "Ese ramo ya existe."
    data["ramos"][name] = {"evaluaciones": []}
    save_data(data)
    return True, "Ramo agregado."

def rename_ramo(old: str, new: str) -> Tuple[bool, str]:
    old = (old or "").strip()
    new = (new or "").strip()
    if not old or not new:
        return False, "Nombre inválido."
    data = load_data()
    if old not in data["ramos"]:
        return False, "El ramo no existe."
    if new in data["ramos"]:
        return False, "Ya existe un ramo con ese nombre."

    data["ramos"][new] = data["ramos"].pop(old)
    if data.get("ramo_activo") == old:
        data["ramo_activo"] = new
    save_data(data)
    return True, "Ramo renombrado."

def delete_ramo(ramo: str) -> Tuple[bool, str]:
    r = (ramo or "").strip()
    data = load_data()
    if r not in data["ramos"]:
        return False, "El ramo no existe."
    if len(data["ramos"]) <= 1:
        return False, "No puedes borrar el último ramo."

    del data["ramos"][r]
    if data.get("ramo_activo") == r:
        data["ramo_activo"] = list(data["ramos"].keys())[0]
    save_data(data)
    return True, "Ramo eliminado."

# =========================
# Evaluaciones
# =========================
def get_evaluaciones(ramo: Optional[str] = None) -> List[Dict]:
    data = load_data()
    r = ramo or data.get("ramo_activo", "Matemática")
    evs = data["ramos"].get(r, {}).get("evaluaciones", [])
    return evs if isinstance(evs, list) else []

def add_evaluacion(nota: float, peso: Optional[float] = None, ramo: Optional[str] = None) -> Tuple[bool, str]:
    n = float(nota)
    if not (1.0 <= n <= 7.0):
        return False, "Nota fuera de rango."

    # En escolar bloqueamos peso por seguridad
    if not ponderacion_habilitada() and peso is not None:
        return False, "Escolar no usa ponderación."

    data = load_data()
    r = ramo or data.get("ramo_activo", "Matemática")
    if r not in data["ramos"]:
        return False, "Ramo inválido."

    item = {"nota": n}
    if peso is not None:
        p = float(peso)
        if not (0.0 < p <= 100.0):
            return False, "Peso inválido."
        item["peso"] = p

    data["ramos"][r]["evaluaciones"].append(item)
    save_data(data)
    return True, "OK"

def delete_evaluacion(idx: int, ramo: Optional[str] = None) -> Tuple[bool, str]:
    data = load_data()
    r = ramo or data.get("ramo_activo", "Matemática")
    evs = data["ramos"].get(r, {}).get("evaluaciones", [])
    if not evs:
        return False, "No hay evaluaciones."
    if idx < 0 or idx >= len(evs):
        return False, "Índice inválido."
    evs.pop(idx)
    save_data(data)
    return True, "Evaluación borrada."

def clear_evaluaciones(ramo: Optional[str] = None) -> None:
    data = load_data()
    r = ramo or data.get("ramo_activo", "Matemática")
    if r in data["ramos"]:
        data["ramos"][r]["evaluaciones"] = []
        save_data(data)

# =========================
# Promedios
# =========================
def promedio_ponderado(evs: List[Dict]) -> Tuple[Optional[float], str]:
    if not evs:
        return None, "SIN_DATOS"

    con_peso = [ev for ev in evs if isinstance(ev, dict) and "peso" in ev]
    sin_peso = [ev for ev in evs if isinstance(ev, dict) and "peso" not in ev]

    if con_peso and sin_peso:
        return None, "INCOMPLETO"

    if not con_peso:
        notas = [float(ev["nota"]) for ev in evs if isinstance(ev, dict) and "nota" in ev]
        if not notas:
            return None, "SIN_DATOS"
        return sum(notas) / len(notas), "OK"

    suma = sum(float(ev["peso"]) for ev in con_peso)
    if not (100.0 - TOL_PESOS <= suma <= 100.0 + TOL_PESOS):
        return None, "PESOS_INVALIDOS"

    prom = sum(float(ev["nota"]) * (float(ev["peso"]) / 100.0) for ev in con_peso)
    return prom, "OK"

def promedio_ramo(ramo: Optional[str] = None) -> Tuple[Optional[float], str]:
    return promedio_ponderado(get_evaluaciones(ramo))

def promedio_global() -> Tuple[Optional[float], str]:
    data = load_data()
    ramos = list(data.get("ramos", {}).keys())
    proms: List[float] = []
    for r in ramos:
        p, st = promedio_ramo(r)
        if p is not None and st == "OK":
            proms.append(p)
    if not proms:
        return None, "SIN_DATOS"
    return sum(proms) / len(proms), "OK"

def debug_data_path() -> str:
    return str(DATA_PATH)