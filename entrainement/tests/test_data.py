import json
from pathlib import Path

import pytest

from gherkin_ft.config import DataConfig, apply_overrides, load_config
from gherkin_ft.data import (
    DataReport,
    deduplicate,
    load_dataset_splits,
    load_pairs,
    split_pairs,
    subsample,
)
from gherkin_ft.prompts import build_training_example

FIX = Path(__file__).parent / "fixtures"


def cfg(**kw) -> DataConfig:
    base = dict(train_files=[str(FIX / "paires.jsonl")], metadata_files=[str(FIX / "regles.jsonl")])
    base.update(kw)
    return DataConfig(**base)


def test_metadata_join_gives_groups_and_skips_long_fields():
    pairs = load_pairs(cfg().train_files, cfg(), DataReport())
    assert len(pairs) == 6
    assert {p.group for p in pairs} == {"domaine:smic", "domaine:aides_logement", "domaine:allocations_familiales"}
    assert "texte_loi" not in pairs[0].meta and pairs[0].meta["notes"] == "fixture"


def test_group_split_has_no_leakage_and_is_deterministic():
    train, evals, report = load_dataset_splits(cfg(eval_ratio=0.3))
    assert report.split_method == "par groupe"
    assert evals and train
    assert not ({p.group for p in train} & {p.group for p in evals})
    train2, evals2, _ = load_dataset_splits(cfg(eval_ratio=0.3))
    assert [p.id for p in evals] == [p.id for p in evals2]


def test_without_groups_falls_back_to_pair_split_with_warning():
    train, evals, report = load_dataset_splits(cfg(metadata_files=[], eval_ratio=0.34))
    assert report.split_method == "par paire"
    assert len(evals) == 2 and len(train) == 4
    assert report.warnings


def test_explicit_eval_files_remove_same_group_from_train(tmp_path):
    eval_file = tmp_path / "eval.jsonl"
    first = json.loads((FIX / "paires.jsonl").read_text(encoding="utf-8").splitlines()[0])
    first["id"] = "EVAL-1"
    first["specification"] += " (variante)"
    first["domaine"] = "smic"
    eval_file.write_text(json.dumps(first, ensure_ascii=False) + "\n", encoding="utf-8")
    train, evals, report = load_dataset_splits(cfg(eval_files=[str(eval_file)]))
    assert [p.id for p in evals] == ["EVAL-1"]
    assert all(p.group != "domaine:smic" for p in train)
    assert report.dropped["groupe présent dans l'évaluation"] == 2


def test_manifest_freezes_eval_set():
    train, evals, report = load_dataset_splits(cfg(eval_ratio=0.3))
    manifest = {"eval_ids": [p.id for p in evals], "eval_groups": sorted({p.group for p in evals})}
    report2 = DataReport()
    pairs = load_pairs(cfg().train_files, cfg(), report2)
    t2, e2 = split_pairs(pairs, cfg(), report2, manifest)
    assert [p.id for p in sorted(e2, key=lambda p: p.id)] == [p.id for p in evals]


def test_invalid_gherkin_and_duplicates_are_dropped(tmp_path):
    f = tmp_path / "p.jsonl"
    good = json.loads((FIX / "paires.jsonl").read_text(encoding="utf-8").splitlines()[0])
    rows = [
        good,
        {**good, "id": "DUP"},
        {"id": "BAD", "specification": "x", "gherkin": "pas du gherkin"},
        {"id": "VIDE", "specification": "", "gherkin": good["gherkin"]},
        {"id": "FENCE", "spec": "autre spec", "output": "```gherkin\n" + good["gherkin"] + "```"},
    ]
    f.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    report = DataReport()
    c = DataConfig(train_files=[str(f)])
    pairs = deduplicate(load_pairs(c.train_files, c, report), report)
    assert sorted(p.id for p in pairs) == ["FENCE", "RG-01"]
    assert report.dropped["gherkin invalide"] == 1
    assert report.dropped["spécification ou gherkin absent"] == 1
    assert report.dropped["spécification en double"] == 1
    assert not next(p for p in pairs if p.id == "FENCE").gherkin.startswith("```")


def test_subsample_is_deterministic():
    pairs = load_pairs(cfg().train_files, cfg(), DataReport())
    a = subsample(pairs, 3, seed=1)
    assert len(a) == 3 and [p.id for p in a] == [p.id for p in subsample(pairs, 3, seed=1)]


def test_training_example_format():
    ex = build_training_example("RG-01", "Spéc.", "# language: fr\n", "Système")
    assert [m["role"] for m in ex["prompt"]] == ["system", "user"]
    assert ex["prompt"][1]["content"] == "Règle : RG-01\n\nSpécification :\nSpéc."
    assert ex["completion"] == [{"role": "assistant", "content": "# language: fr\n"}]


def test_config_overrides_and_unknown_keys(tmp_path):
    c = load_config(Path(__file__).parents[1] / "configs" / "ministral3b_lora.yaml",
                    ["training.learning_rate=2e-4", "data.train_limit=500", "lora.r=8"])
    assert c.training.learning_rate == 2e-4 and c.data.train_limit == 500 and c.lora.r == 8
    with pytest.raises(ValueError, match="inconnue"):
        load_config(None, ["training.learnin_rate=1"])
    assert apply_overrides({}, ["a.b=[1, 2]"]) == {"a": {"b": [1, 2]}}


def test_qlora_config_loads():
    c = load_config(Path(__file__).parents[1] / "configs" / "ministral3b_qlora.yaml")
    assert c.model.load_in_4bit and c.training.optim == "paged_adamw_8bit"
