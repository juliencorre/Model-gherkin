"""Chargement, nettoyage et découpage des paires (spécification, Gherkin).

Format d'entrée : JSONL (ou JSON liste), une paire par ligne, comme produit par la préparation du corpus :
    {"id": "RG-01", "specification": "...", "gherkin": "# language: fr\\n...", "notes": "...", "domaine": "smic"}

Le découpage train/eval se fait par groupe (dispositif juridique, domaine ou fichier source) et jamais par
scénario, pour éviter qu'une même règle se retrouve des deux côtés.
"""

from __future__ import annotations

import glob
import hashlib
import json
import logging
import random
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .config import DataConfig
from .quality import analyze_gherkin, quality_score, strip_markdown_fence

log = logging.getLogger(__name__)

ID_KEYS = ("id", "identifiant", "rule_id", "regle")
SPEC_KEYS = ("specification", "spécification", "spec", "exigence", "input")
GHERKIN_KEYS = ("gherkin", "feature", "output", "completion")
TRAIN_SPLITS = {"train", "entrainement", "entraînement"}
EVAL_SPLITS = {"eval", "evaluation", "évaluation", "validation", "valid", "dev", "test"}


@dataclass
class Pair:
    id: str
    specification: str
    gherkin: str
    group: str
    split: str | None = None
    source_file: str = ""
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DataReport:
    files: list[str] = field(default_factory=list)
    read: int = 0
    dropped: Counter = field(default_factory=Counter)
    dropped_ids: dict[str, list[str]] = field(default_factory=dict)
    group_fallback_to_id: int = 0
    split_method: str = ""
    warnings: list[str] = field(default_factory=list)

    def drop(self, reason: str, pair_id: str) -> None:
        self.dropped[reason] += 1
        self.dropped_ids.setdefault(reason, []).append(pair_id)

    def warn(self, message: str) -> None:
        log.warning(message)
        self.warnings.append(message)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["dropped"] = dict(self.dropped)
        return d


def expand_paths(patterns: list[str]) -> list[Path]:
    """Motifs glob (`**` accepté), fichiers ou dossiers (tous les .jsonl/.json qu'ils contiennent)."""
    paths: list[Path] = []
    for pattern in patterns:
        p = Path(pattern)
        if p.is_dir():
            matches = sorted([*p.rglob("*.jsonl"), *p.rglob("*.json")])
        else:
            matches = sorted(Path(m) for m in glob.glob(pattern, recursive=True))
        if not matches:
            log.warning("Aucun fichier pour « %s »", pattern)
        paths.extend(m for m in matches if m not in paths)
    return paths


def read_records(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    records = []
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{n} : JSON invalide ({e})") from e
    return records


def _first(record: dict, override: str | None, keys: tuple[str, ...]) -> str:
    for key in ((override,) if override else keys):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "  ")
    return "\n".join(line.rstrip() for line in text.strip().split("\n"))


def clean_gherkin(text: str) -> str:
    text, _ = strip_markdown_fence(normalize_text(text))
    return text.strip() + "\n"


def _dedup_key(text: str) -> str:
    return hashlib.sha1(re.sub(r"\s+", " ", text.lower()).strip().encode()).hexdigest()


def _record_to_pair(record: dict, cfg: DataConfig, source: Path, index: int, metadata: dict[str, dict]) -> Pair | None:
    pair_id = _first(record, cfg.fields.get("id"), ID_KEYS) or f"{source.stem}#{index}"
    meta_extra = metadata.get(pair_id, {})
    merged = {**meta_extra, **{k: v for k, v in record.items() if v not in (None, "")}}
    spec = _first(merged, cfg.fields.get("specification"), SPEC_KEYS)
    gherkin = _first(merged, cfg.fields.get("gherkin"), GHERKIN_KEYS)
    if not spec or not gherkin:
        return None
    group = ""
    for key in cfg.group_by:
        value = merged.get(key)
        if isinstance(value, str) and value.strip():
            group = f"{key}:{value.strip()}"
            break
    split = merged.get(cfg.fields.get("split", "split"))
    split = split.strip().lower() if isinstance(split, str) else None
    if split in TRAIN_SPLITS:
        split = "train"
    elif split in EVAL_SPLITS:
        split = "eval"
    else:
        split = None
    used = {"specification", "gherkin", "id"} | set(SPEC_KEYS) | set(GHERKIN_KEYS) | set(ID_KEYS)
    # Métadonnées courtes seulement (provenance, licence, domaine...), pas les textes de loi ou le code joints.
    meta = {
        k: v for k, v in merged.items()
        if k not in used and (isinstance(v, (int, float, bool)) or (isinstance(v, str) and len(v) <= 200))
    }
    return Pair(
        id=pair_id,
        specification=normalize_text(spec),
        gherkin=clean_gherkin(gherkin),
        group=group,
        split=split,
        source_file=str(source),
        meta=meta,
    )


def load_metadata(patterns: list[str], id_key: str | None = None) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for path in expand_paths(patterns):
        for record in read_records(path):
            rid = _first(record, id_key, ID_KEYS)
            if rid:
                index.setdefault(rid, record)
    return index


def load_pairs(patterns: list[str], cfg: DataConfig, report: DataReport, forced_split: str | None = None) -> list[Pair]:
    """Lit, nettoie et filtre les paires. Les rejets sont comptés dans `report`."""
    metadata = load_metadata(cfg.metadata_files, cfg.fields.get("id")) if cfg.metadata_files else {}
    pairs: list[Pair] = []
    for path in expand_paths(patterns):
        report.files.append(str(path))
        for i, record in enumerate(read_records(path)):
            report.read += 1
            pair = _record_to_pair(record, cfg, path, i, metadata)
            if pair is None:
                report.drop("spécification ou gherkin absent", str(record.get("id", f"{path.name}#{i}")))
                continue
            if forced_split:
                pair.split = forced_split
            if not pair.group:
                pair.group = f"id:{pair.id}"
                report.group_fallback_to_id += 1
            if cfg.require_valid_gherkin or cfg.min_reference_score > 0:
                analysis = analyze_gherkin(pair.gherkin, pair.id, expected_language=cfg.expected_language)
                if cfg.require_valid_gherkin and not (analysis.syntax_ok and analysis.language_ok):
                    report.drop("gherkin invalide", pair.id)
                    continue
                if quality_score(analysis, pair.id) < cfg.min_reference_score:
                    report.drop("score de référence trop bas", pair.id)
                    continue
            pairs.append(pair)
    return pairs


def deduplicate(pairs: list[Pair], report: DataReport) -> list[Pair]:
    """Supprime les spécifications en double. En cas de doublon train/eval, l'exemplaire d'évaluation est gardé."""
    pairs = sorted(pairs, key=lambda p: (p.split != "eval",))  # les paires d'éval d'abord
    seen: set[str] = set()
    kept = []
    for pair in pairs:
        key = _dedup_key(pair.specification)
        if key in seen:
            report.drop("spécification en double", pair.id)
            continue
        seen.add(key)
        kept.append(pair)
    return kept


def _stable_order(items: list[str], seed: int) -> list[str]:
    return sorted(items, key=lambda x: hashlib.sha1(f"{seed}:{x}".encode()).hexdigest())


def split_pairs(
    pairs: list[Pair], cfg: DataConfig, report: DataReport, manifest: dict | None = None
) -> tuple[list[Pair], list[Pair]]:
    """Répartit les paires en train/eval, par groupe, de façon déterministe."""
    if manifest:
        eval_ids = set(manifest.get("eval_ids", []))
        eval_groups = set(manifest.get("eval_groups", []))
        report.split_method = "manifest"
        train, evals = [], []
        for p in pairs:
            if p.id in eval_ids or p.split == "eval":
                evals.append(p)
            elif p.group in eval_groups:
                report.drop("groupe réservé à l'évaluation (manifest)", p.id)
            else:
                train.append(p)
        return train, evals

    explicit_eval = [p for p in pairs if p.split == "eval"]
    explicit_train = [p for p in pairs if p.split == "train"]
    free = [p for p in pairs if p.split is None]

    if explicit_eval:
        # Jeu d'évaluation fourni (champ `split` ou `eval_files`) : pas de découpage automatique.
        report.split_method = "explicite"
        eval_groups = {p.group for p in explicit_eval}
        train = []
        for p in explicit_train + free:
            if p.group in eval_groups and not p.group.startswith("id:"):
                report.drop("groupe présent dans l'évaluation", p.id)
            else:
                train.append(p)
        return train, explicit_eval

    groups: dict[str, list[Pair]] = {}
    for p in free:
        groups.setdefault(p.group, []).append(p)
    target = round(cfg.eval_ratio * len(free))
    if cfg.eval_ratio > 0 and len(free) >= 2:
        target = max(1, target)
    if target == 0:
        report.split_method = "aucun"
        return explicit_train + free, []

    real_groups = [g for g in groups if not g.startswith("id:")]
    if len(real_groups) < 2:
        report.warn(
            "Moins de deux groupes (dispositifs) identifiés : découpage paire par paire, avec un risque de fuite "
            "entre entraînement et évaluation. Renseignez un champ de groupe (data.group_by) ou data.metadata_files."
        )
        report.split_method = "par paire"
        order = _stable_order([p.id for p in free], cfg.seed)
        eval_ids = set(order[:target])
        return explicit_train + [p for p in free if p.id not in eval_ids], [p for p in free if p.id in eval_ids]

    report.split_method = "par groupe"
    eval_groups: list[str] = []
    count = 0
    for g in _stable_order(list(groups), cfg.seed):
        if count >= target:
            break
        if count + len(groups[g]) > max(1.5 * target, 1):  # groupe trop gros pour la cible
            continue
        if len(eval_groups) + 1 >= len(groups):  # garder au moins un groupe pour l'entraînement
            break
        eval_groups.append(g)
        count += len(groups[g])
    if not eval_groups:
        smallest = min(groups, key=lambda g: (len(groups[g]), g))
        eval_groups.append(smallest)
        report.warn(
            f"Aucun groupe assez petit pour viser {target} paires d'évaluation : le plus petit groupe ({smallest}, "
            f"{len(groups[smallest])} paires) sert d'évaluation."
        )
    evals = [p for g in eval_groups for p in groups[g]]
    train = explicit_train + [p for g in groups if g not in eval_groups for p in groups[g]]
    return train, evals


def subsample(pairs: list[Pair], limit: int | None, seed: int) -> list[Pair]:
    if not limit or limit >= len(pairs):
        return pairs
    rng = random.Random(seed)
    return sorted(rng.sample(sorted(pairs, key=lambda p: p.id), limit), key=lambda p: p.id)


def write_jsonl(pairs: list[Pair], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p.to_dict(), ensure_ascii=False) + "\n")


def read_pairs_jsonl(path: Path) -> list[Pair]:
    return [Pair(**r) for r in read_records(Path(path))]


def build_manifest(train: list[Pair], evals: list[Pair], report: DataReport) -> dict:
    return {
        "split_method": report.split_method,
        "train_ids": [p.id for p in train],
        "eval_ids": [p.id for p in evals],
        "train_groups": sorted({p.group for p in train}),
        "eval_groups": sorted({p.group for p in evals}),
    }


def load_dataset_splits(cfg: DataConfig, apply_limit: bool = True) -> tuple[list[Pair], list[Pair], DataReport]:
    """Point d'entrée : charge les fichiers, filtre, dédoublonne et découpe.

    `apply_limit=False` laisse `train_limit` à l'appelant (qui l'applique après le filtre de longueur)."""
    report = DataReport()
    pairs = load_pairs(cfg.train_files, cfg, report)
    if cfg.eval_files:
        pairs += load_pairs(cfg.eval_files, cfg, report, forced_split="eval")
    if not pairs:
        raise ValueError(f"Aucune paire exploitable dans {cfg.train_files} (voir le rapport : {report.to_dict()})")
    pairs = deduplicate(pairs, report)
    manifest = None
    if cfg.split_manifest:
        manifest = json.loads(Path(cfg.split_manifest).read_text(encoding="utf-8"))
    train, evals = split_pairs(pairs, cfg, report, manifest)
    if apply_limit:
        train = subsample(train, cfg.train_limit, cfg.seed)
    if report.group_fallback_to_id:
        report.warn(
            f"{report.group_fallback_to_id} paire(s) sans champ de groupe {cfg.group_by} : chacune forme son propre groupe."
        )
    return sorted(train, key=lambda p: p.id), sorted(evals, key=lambda p: p.id), report


def filter_by_length(pairs: list[Pair], lengths: list[int], max_length: int, report: DataReport) -> list[Pair]:
    """Écarte les paires trop longues plutôt que de les tronquer (le modèle apprendrait des Gherkin coupés)."""
    kept = []
    for pair, n in zip(pairs, lengths):
        if n > max_length:
            report.drop(f"plus de {max_length} tokens", pair.id)
        else:
            kept.append(pair)
    return kept


def length_stats(lengths: list[int]) -> dict:
    if not lengths:
        return {}
    s = sorted(lengths)

    def pct(q: float) -> int:
        return s[min(len(s) - 1, int(q * (len(s) - 1) + 0.5))]

    return {"n": len(s), "min": s[0], "median": pct(0.5), "p95": pct(0.95), "max": s[-1]}
