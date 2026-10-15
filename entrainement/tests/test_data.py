import json
import re
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
    base = dict(train_files=[str(FIX / "paires.jsonl")], metadata_files=[str(FIX / "regles.jsonl")],
                eval_files=[], test_files=[])
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
    train, evals, report = load_dataset_splits(cfg(eval_files=[str(eval_file)], drop_train_groups_in_eval=True))
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
    c = DataConfig(train_files=[str(f)], eval_files=[], test_files=[])
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


def to_messages(record: dict, system: str = "Système SFT") -> dict:
    """Paire pilote convertie au format `messages` de data/sft (tags @RG retirés, domaine dans `meta`)."""
    gherkin = re.sub(r" ?@RG-\d+", "", record["gherkin"])
    user = f"Spécification :\n{record['specification']}\n\nRédige le fichier Gherkin (en français) qui teste cette spécification."
    return {"id": f"pilote-{record['id']}", "meta": {"domaine": record["domaine"], "niveau": "A"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user},
                         {"role": "assistant", "content": gherkin}]}


def test_messages_format_with_explicit_val_and_test(tmp_path):
    records = [json.loads(l) for l in (FIX / "paires.jsonl").read_text(encoding="utf-8").splitlines()]
    domains = {json.loads(l)["id"]: json.loads(l)["domaine"] for l in (FIX / "regles.jsonl").read_text(encoding="utf-8").splitlines()}
    msgs = [to_messages({**r, "domaine": domains[r["id"]]}) for r in records]
    for name, rows in (("train", msgs[:4]), ("val", msgs[4:5]), ("test", msgs[5:])):
        (tmp_path / f"{name}.jsonl").write_text("\n".join(json.dumps(m, ensure_ascii=False) for m in rows), encoding="utf-8")
    c = DataConfig(train_files=[str(tmp_path / "train.jsonl")], eval_files=[str(tmp_path / "val.jsonl")],
                   test_files=[str(tmp_path / "test.jsonl")])
    train, evals, report = load_dataset_splits(c)
    assert (len(train), len(evals), len(report.test_pairs)) == (4, 1, 1)  # domaines partagés : rien de retiré
    assert report.split_method == "explicite" and not report.dropped
    assert train[0].group.startswith("domaine:") and train[0].meta["niveau"] == "A"
    # La spécification est isolée de la consigne ; le prompt des données est gardé pour l'entraînement.
    assert train[0].specification == records[0]["specification"]
    assert [m["role"] for m in train[0].prompt] == ["system", "user"]
    assert report.prompt_template == {
        "system_prompt": "Système SFT",
        "user_template": "Spécification :\n{specification}\n\nRédige le fichier Gherkin (en français) qui teste cette spécification.",
    }
    # Sans tag @RG dans les références, le critère « tag de règle » ne s'applique pas.
    assert train[0].rule_tag_id is None
    pilot = load_pairs([str(FIX / "paires.jsonl")], cfg(), DataReport())
    assert pilot[0].rule_tag_id == "RG-01"
    from gherkin_ft.evaluation import score_prediction
    row = score_prediction(train[0], train[0].gherkin, True, "fr")
    assert row["score"] == row["score_reference"] == 1.0
    from gherkin_ft.prompts import build_user_prompt
    assert build_user_prompt("x", records[0]["specification"], report.prompt_template["user_template"]) == train[0].prompt[1]["content"]
