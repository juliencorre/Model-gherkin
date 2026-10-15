"""Interface web : API, protections, et vrais lancements d'entraînement (sous-processus, modèle miniature)."""

import json
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from gherkin_ft.ihm import IhmServer, TrainingJobs, tail_log
from tiny_model import build_tiny_ministral3, corpus_from_jsonl

TESTS = Path(__file__).parent
FIX = TESTS / "fixtures"
CONFIGS = TESTS.parent / "configs"


class Client:
    def __init__(self, base: str, token: str | None = None):
        self.base, self.token = base, token

    def request(self, path, body=None, headers=None, raw=False):
        h = dict(headers or {})
        if self.token:
            h.setdefault("X-Jeton", self.token)
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            h.setdefault("Content-Type", "application/json")
            h.setdefault("X-Gherkin-FT", "1")
        req = urllib.request.Request(self.base + path, data=data, headers=h, method="POST" if body is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                payload = r.read()
                return r.status, (payload if raw else json.loads(payload))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")


@pytest.fixture
def server(tmp_path):
    jobs = TrainingJobs(tmp_path / "runs", CONFIGS, command=[sys.executable, str(TESTS / "cpu_cli.py")])
    srv = IhmServer("127.0.0.1", 0, jobs)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv, Client(f"http://127.0.0.1:{srv.server_address[1]}")
    for proc in jobs._procs.values():  # ne laisse aucun entraînement orphelin
        if proc.poll() is None:
            proc.kill()
    srv.shutdown()
    srv.server_close()


def tiny_config(client, model_dir, **training):
    status, data = client.request("/api/config?nom=ministral3b_lora.yaml")
    assert status == 200
    cfg = data["config"]
    cfg["model"]["name_or_path"] = str(model_dir)
    cfg["data"].update(train_files=[str(FIX / "paires.jsonl")], metadata_files=[str(FIX / "regles.jsonl")],
                       eval_files=[], test_files=[], eval_ratio=0.3, max_length=1024)
    cfg["training"].update({**dict(max_steps=4, eval_steps=2, logging_steps=1, per_device_train_batch_size=2,
                                   gradient_accumulation_steps=1, learning_rate=1e-3, optim="adamw_torch",
                                   report_to=["none"], dataloader_num_workers=0), **training})
    cfg["lora"].update(r=4, alpha=8)
    cfg["eval"].update(probe_samples=2, probe_max_new_tokens=8, max_new_tokens=8, batch_size=2)
    return cfg


def wait_for(client, name, predicate, timeout=180):
    deadline = time.time() + timeout
    details = None
    while time.time() < deadline:
        status, details = client.request(f"/api/runs/{name}")
        if status == 200 and predicate(details):
            return details
        time.sleep(0.5)
    raise AssertionError(f"Délai dépassé pour {name} : {json.dumps(details, ensure_ascii=False)[:2000]}")


def test_page_state_configs_and_security(server):
    srv, client = server
    status, html = client.request("/", raw=True)
    assert status == 200 and b"Entra\xc3\xaenement Gherkin" in html
    status, etat = client.request("/api/etat")
    assert status == 200 and etat["actif"] is None and "ministral3b_lora.yaml" in etat["configs"]
    status, data = client.request("/api/config")
    assert status == 200 and data["config"]["model"]["name_or_path"].endswith("-BF16")
    assert client.request("/api/config?nom=inconnu.yaml")[0] == 404
    # POST sans l'en-tête de la page (requête forgée par un autre site) : refusé
    assert client.request("/api/apercu", {"config": {}}, headers={"X-Gherkin-FT": "0"})[0] == 403
    # En-tête Host étranger (DNS rebinding) : refusé
    assert client.request("/api/etat", headers={"Host": "evil.example:7860"})[0] == 403
    # Nom de run dangereux : refusé
    assert client.request("/api/runs/..%2F..%2Fetc")[0] == 400


def test_token_required_when_set(tmp_path):
    jobs = TrainingJobs(tmp_path / "runs", CONFIGS)
    srv = IhmServer("127.0.0.1", 0, jobs, token="secret")
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        assert Client(base).request("/api/etat")[0] == 403
        assert Client(base, token="secret").request("/api/etat")[0] == 200
        assert Client(base).request("/api/etat?jeton=secret")[0] == 200
        assert srv.url.endswith("?jeton=secret")
    finally:
        srv.shutdown()
        srv.server_close()


def test_preview_counts_pairs_and_limit(server):
    _, client = server
    status, data = client.request("/api/config")
    cfg = data["config"]
    cfg["data"].update(train_files=[str(FIX / "paires.jsonl")], metadata_files=[str(FIX / "regles.jsonl")],
                       eval_files=[], test_files=[], eval_ratio=0.3, train_limit=3)
    status, p = client.request("/api/apercu", {"config": cfg})
    assert status == 200, p
    assert p["lues"] == 6 and p["disponibles_train"] + p["eval"] == 6
    assert p["utilisees_train"] == 3 and p["methode"] == "par groupe"
    assert not set(p["groupes_train"]) & set(p["groupes_eval"])
    cfg["training"]["learnin_rate"] = 1
    status, err = client.request("/api/apercu", {"config": cfg})
    assert status == 400 and "inconnue" in err["erreur"]
    cfg["training"].pop("learnin_rate")
    cfg["data"]["train_files"] = ["nexiste/pas/*.jsonl"]
    assert client.request("/api/apercu", {"config": cfg})[0] == 400


@pytest.mark.slow
def test_launch_follow_stop_and_resume(server, tmp_path):
    srv, client = server
    model_dir = build_tiny_ministral3(tmp_path / "tiny", corpus_from_jsonl(FIX / "paires.jsonl"))

    # 1. Entraînement complet sur 3 paires (nombre choisi dans l'interface), suivi jusqu'au bout
    cfg = tiny_config(client, model_dir)
    cfg["data"]["train_limit"] = 3
    status, res = client.request("/api/lancer", {"config": cfg, "nom": "essai-1"})
    assert status == 200, res
    assert client.request("/api/etat")[1]["actif"] == "essai-1"
    # un seul entraînement à la fois
    status, err = client.request("/api/lancer", {"config": cfg, "nom": "essai-2"})
    assert status == 409 and "déjà en cours" in err["erreur"]
    d = wait_for(client, "essai-1", lambda d: d["statut"] not in ("en cours",))
    assert d["statut"] == "terminé", d["journal"]
    p = d["progression"]
    assert p["step"] == p["max_steps"] == 4 and p["train_pairs"] == 3 and p["eval_pairs"] == 2
    assert len(d["donnees"] and open(Path(d["chemin"]) / "data" / "train.jsonl").readlines()) == 3
    assert any("loss" in h for h in p["history"]) and any("eval_score_qualite" in h for h in p["history"])
    assert d["metriques"]["n"] == 2 and d["rapport"].startswith("# Évaluation")
    runs = client.request("/api/runs")[1]["runs"]
    assert runs[0]["nom"] == "essai-1" and runs[0]["adaptateur"] and runs[0]["manifeste"]
    # même nom refusé, réutilisation de la config du run possible
    assert client.request("/api/lancer", {"config": cfg, "nom": "essai-1"})[0] == 409
    status, data = client.request("/api/config?run=essai-1")
    assert status == 200 and data["config"]["lora"]["r"] == 4

    # 2. Arrêt propre demandé pendant l'entraînement : adaptateur enregistré, statut « arrêté »
    cfg2 = tiny_config(client, model_dir, max_steps=400, eval_steps=5)
    cfg2["data"]["split_manifest"] = d["chemin"] + "/data/manifest.json"  # même jeu d'évaluation
    assert client.request("/api/lancer", {"config": cfg2, "nom": "essai-2"})[0] == 200
    wait_for(client, "essai-2", lambda d: (d["progression"] or {}).get("step", 0) >= 6)
    status, res = client.request("/api/arreter", {"nom": "essai-2"})
    assert status == 200 and res["arret"] == "demandé"
    d2 = wait_for(client, "essai-2", lambda d: not d["actif"])
    assert d2["statut"] == "arrêté", d2["journal"]
    assert d2["progression"]["step"] < 400 and d2["checkpoints"]
    assert (Path(d2["chemin"]) / "adapter" / "adapter_config.json").exists()

    # 3. Reprise depuis le dernier checkpoint, puis arrêt forcé : statut « interrompu »
    status, res = client.request("/api/lancer", {"config": cfg2, "nom": "essai-2", "reprendre": True})
    assert status == 200, res
    d3 = wait_for(client, "essai-2", lambda d: (d["progression"] or {}).get("phase") == "entraînement")
    assert d3["progression"]["step"] >= 5  # reprise au checkpoint, pas à zéro
    assert any(h.get("step", 0) <= 5 for h in d3["progression"]["history"])  # historique restauré
    status, res = client.request("/api/arreter", {"nom": "essai-2", "forcer": True})
    assert status == 200 and res["arret"] == "forcé"
    d4 = wait_for(client, "essai-2", lambda d: not d["actif"], timeout=30)
    assert d4["statut"] == "interrompu"
    assert client.request("/api/arreter", {"nom": "essai-2"})[0] == 400  # plus rien à arrêter

    # 4. Un serveur redémarré retrouve un entraînement en cours
    assert client.request("/api/lancer", {"config": tiny_config(client, model_dir), "nom": "essai-3"})[0] == 200
    fresh = TrainingJobs(srv.jobs.runs_dir, CONFIGS)
    assert fresh.active() == "essai-3"
    wait_for(client, "essai-3", lambda d: not d["actif"])
    assert fresh.active() is None


def test_tail_log_cleans_progress_bars(tmp_path):
    f = tmp_path / "log"
    f.write_text("a\n\x1b[32mvert\x1b[0m\n 10%|█  \r 50%|█████\r100%|██████████\nfin\n", encoding="utf-8")
    assert tail_log(f) == "a\nvert\n100%|██████████\nfin"
