"""Chaîne complète sur CPU avec un Ministral 3 miniature : train → evaluate → merge → generate."""

import json
from pathlib import Path

import pytest

from gherkin_ft.cli import main
from gherkin_ft.config import load_config
from gherkin_ft.train import run_training
from tiny_model import build_tiny_ministral3, corpus_from_jsonl

FIX = Path(__file__).parent / "fixtures"


@pytest.mark.slow
def test_train_evaluate_merge_generate(tmp_path):
    pytest.importorskip("torch")
    model_dir = build_tiny_ministral3(tmp_path / "tiny", corpus_from_jsonl(FIX / "paires.jsonl"))
    run_dir = tmp_path / "run"
    cfg = load_config(None, [
        f"model.name_or_path={model_dir}",
        f"data.train_files=[{FIX / 'paires.jsonl'}]",
        f"data.metadata_files=[{FIX / 'regles.jsonl'}]",
        "data.eval_files=[]",
        "data.test_files=[]",
        "data.eval_ratio=0.3",
        "data.max_length=1024",
        f"training.output_dir={run_dir}",
        "training.max_steps=4",
        "training.eval_steps=2",
        "training.logging_steps=1",
        "training.per_device_train_batch_size=2",
        "training.gradient_accumulation_steps=1",
        "training.learning_rate=1e-3",
        "training.optim=adamw_torch",
        "training.report_to=[none]",
        "training.dataloader_num_workers=0",
        "lora.r=4",
        "lora.alpha=8",
        "eval.probe_samples=2",
        "eval.probe_max_new_tokens=8",
        "eval.max_new_tokens=8",
        "eval.batch_size=2",
    ])
    adapter = run_training(cfg)

    adapter_cfg = json.loads((adapter / "adapter_config.json").read_text())
    assert adapter_cfg["r"] == 4
    info = json.loads((adapter / "gherkin_ft.json").read_text())
    assert info["base_model"] == str(model_dir) and info["system_prompt"]
    manifest = json.loads((run_dir / "data" / "manifest.json").read_text())
    assert manifest["eval_ids"] and not set(manifest["train_groups"]) & set(manifest["eval_groups"])
    train_metrics = json.loads((run_dir / "metrics_entrainement.json").read_text())
    assert "eval_loss" in train_metrics["eval"] and "eval_score_qualite" in train_metrics["eval"]
    progress = json.loads((run_dir / "progress.json").read_text())
    assert progress["status"] == "terminé" and progress["step"] == progress["max_steps"] == 4
    assert any("loss" in h for h in progress["history"]) and any("eval_score_qualite" in h for h in progress["history"])
    final = json.loads((run_dir / "eval" / "metrics.json").read_text())
    assert final["n"] == len(manifest["eval_ids"]) and "score_qualite" in final
    assert (run_dir / "eval" / "rapport.md").exists()

    # Évaluation séparée (modèle de base vs affiné) puis comparaison.
    assert main(["evaluate", "--adapter", str(adapter), "--max-samples", "1", "--max-new-tokens", "4",
                 "--out", str(tmp_path / "eval_ft")]) == 0
    assert main(["evaluate", "--set", f"model.name_or_path={model_dir}", "--data", str(run_dir / "data" / "eval.jsonl"),
                 "--max-samples", "1", "--max-new-tokens", "4", "--out", str(tmp_path / "eval_base")]) == 0
    assert main(["compare", str(tmp_path / "eval_base" / "metrics.json"),
                 str(tmp_path / "eval_ft" / "metrics.json")]) == 0

    merged = tmp_path / "merged"
    assert main(["merge", "--adapter", str(adapter), "--out", str(merged), "--device", "cpu"]) == 0
    assert (merged / "config.json").exists() and (merged / "gherkin_ft.json").exists()

    # Limite du nombre de paires et arrêt propre demandé dès le premier pas : adaptateur enregistré, statut « arrêté ».
    run2 = tmp_path / "run2"
    run2.mkdir()
    (run2 / "STOP").touch()  # un STOP antérieur au lancement est ignoré...
    cfg.training.output_dir = str(run2)
    cfg.data.train_limit = 2
    cfg.training.max_steps = 50

    from gherkin_ft import progress as progress_mod

    original_init = progress_mod.ProgressWriter.__init__

    def init_then_stop(self, *a, **kw):  # ... puis on demande l'arrêt juste après le démarrage
        original_init(self, *a, **kw)
        self.stop_path.touch()

    progress_mod.ProgressWriter.__init__ = init_then_stop
    try:
        run_training(cfg)
    finally:
        progress_mod.ProgressWriter.__init__ = original_init
    p2 = json.loads((run2 / "progress.json").read_text())
    assert p2["status"] == "arrêté" and p2["step"] == 1 and p2["train_pairs"] == 2
    assert (run2 / "adapter" / "adapter_config.json").exists() and not (run2 / "eval").exists()

    # Le modèle aléatoire n'écrit pas de Gherkin valide : code de retour 1 attendu, mais sans erreur.
    out_file = tmp_path / "sortie.feature"
    code = main(["generate", "--model", str(merged), "--spec", "Le plafond est de 300 €.", "--id", "RG-99",
                 "--max-new-tokens", "6", "--retries", "1", "--out", str(out_file)])
    assert code in (0, 1) and out_file.exists()
