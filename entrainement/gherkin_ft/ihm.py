"""Interface web locale : paramétrer, lancer, suivre et arrêter les entraînements.

Serveur HTTP de la bibliothèque standard (aucune dépendance) servant une page unique (`static/ihm.html`)
et une petite API JSON. L'entraînement tourne dans un processus séparé (`gherkin-ft train`), détaché du
serveur : fermer l'interface n'interrompt pas un entraînement, et la rouvrir le retrouve.

Sécurité : écoute sur 127.0.0.1 par défaut. Les requêtes POST exigent un en-tête propre à la page
(un site tiers ne peut pas les forger depuis le navigateur), l'en-tête Host est contrôlé (DNS rebinding),
et une écoute sur une autre adresse exige un jeton aléatoire affiché au démarrage.
"""

from __future__ import annotations

import ipaddress
import json
import logging
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from collections import Counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import yaml

from .config import Config, _build, load_config, save_config
from .progress import RUNNING, read_progress, request_stop

log = logging.getLogger(__name__)

STATIC_PAGE = Path(__file__).parent / "static" / "ihm.html"
DEFAULT_CONFIGS_DIR = Path(__file__).resolve().parents[1] / "configs"
RUN_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
POST_HEADER = "X-Gherkin-FT"
TOKEN_HEADER = "X-Jeton"
JOB_FILE = "job.json"
OUTPUT_LOG = "sortie.log"


class ApiError(Exception):
    def __init__(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.status = status


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _pid_alive(pid: int, marker: str | None = None) -> bool:
    """Le processus existe-t-il encore ? `marker` (chemin de la config du run) écarte un PID réattribué."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes()
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return True
    if stat.rsplit(")", 1)[-1].split()[0] == "Z":  # zombie : terminé, pas encore récupéré
        return False
    return marker is None or marker.encode() in cmdline


def tail_log(path: Path, lines: int = 80) -> str:
    """Dernières lignes d'un journal, barres de progression (\\r) et codes ANSI nettoyés."""
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 64_000))
            raw = f.read().decode("utf-8", errors="replace")
    except OSError:
        return ""
    out = [ANSI_RE.sub("", line.split("\r")[-1]) for line in raw.split("\n")]
    return "\n".join(out[-lines:]).strip()


_gpu_cache: tuple[float, list | None] = (0.0, None)


def gpu_stats() -> list[dict] | None:
    """Utilisation des GPU via nvidia-smi (mise en cache 2 s). None si nvidia-smi est absent."""
    global _gpu_cache
    if time.time() - _gpu_cache[0] < 2:
        return _gpu_cache[1]
    stats = None
    if shutil.which("nvidia-smi"):
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5, check=True,
            ).stdout
            stats = []
            for line in out.strip().splitlines():
                name, util, used, total, temp, power = [x.strip() for x in line.split(",")]

                def num(x):
                    try:
                        return float(x)
                    except ValueError:
                        return None

                stats.append({"nom": name, "utilisation": num(util), "memoire_utilisee": num(used),
                              "memoire_totale": num(total), "temperature": num(temp), "puissance": num(power)})
        except (OSError, subprocess.SubprocessError, ValueError):
            stats = None
    _gpu_cache = (time.time(), stats)
    return stats


class TrainingJobs:
    """Lance et suit les entraînements (un à la fois : un seul GPU)."""

    def __init__(self, runs_dir: Path, configs_dir: Path = DEFAULT_CONFIGS_DIR, command: list[str] | None = None):
        self.runs_dir = Path(runs_dir)
        self.configs_dir = Path(configs_dir)
        self.command = command or [sys.executable, "-m", "gherkin_ft"]
        self._procs: dict[str, subprocess.Popen] = {}
        self._lock = threading.Lock()

    # --- runs -----------------------------------------------------------------------------------------
    def run_dir(self, name: str) -> Path:
        if not RUN_NAME_RE.match(name or ""):
            raise ApiError("Nom de run invalide : lettres, chiffres, « . », « _ » et « - » seulement (64 max).")
        return self.runs_dir / name

    def _alive(self, name: str) -> bool:
        proc = self._procs.get(name)
        if proc is not None:
            return proc.poll() is None
        job = _read_json(self.runs_dir / name / JOB_FILE)
        if not job or not job.get("pid"):
            return False
        command = job.get("commande") or []
        return _pid_alive(int(job["pid"]), command[-1] if command else None)

    def _status(self, name: str, progress: dict | None) -> str:
        alive = self._alive(name)
        if progress is None:
            return RUNNING if alive else "inconnu"
        status = progress.get("status", "inconnu")
        if status == RUNNING and not alive:
            proc = self._procs.get(name)
            if proc is not None and proc.returncode not in (0, None, -signal.SIGTERM):
                return "erreur"
            return "interrompu"
        return status

    def active(self) -> str | None:
        for name in list(self._procs):
            if self._procs[name].poll() is None:
                return name
        if self.runs_dir.is_dir():
            for d in self.runs_dir.iterdir():
                if (d / JOB_FILE).exists() and self._alive(d.name):
                    return d.name
        return None

    def list_runs(self) -> list[dict]:
        runs = []
        if not self.runs_dir.is_dir():
            return runs
        for d in self.runs_dir.iterdir():
            if not d.is_dir() or not ((d / "progress.json").exists() or (d / "config.yaml").exists()):
                continue
            progress = read_progress(d) or {}
            final = _read_json(d / "eval" / "metrics.json") or {}
            training = _read_json(d / "metrics_entrainement.json") or {}
            evals = [h for h in progress.get("history", []) if "eval_loss" in h]
            runs.append({
                "nom": d.name,
                "statut": self._status(d.name, progress or None),
                "debut": progress.get("started_at"),
                "fin": progress.get("finished_at"),
                "pas": progress.get("step"),
                "pas_max": progress.get("max_steps"),
                "paires_train": progress.get("train_pairs"),
                "paires_eval": progress.get("eval_pairs"),
                "eval_loss": (training.get("eval") or {}).get("eval_loss") or (evals[-1]["eval_loss"] if evals else None),
                "score_qualite": final.get("score_qualite"),
                "syntaxe_ok": final.get("syntaxe_ok"),
                "adaptateur": (d / "adapter" / "adapter_config.json").exists(),
                "checkpoints": any((d / "checkpoints").glob("checkpoint-*")),
                "manifeste": (d / "data" / "manifest.json").exists(),
            })
        runs.sort(key=lambda r: r["debut"] or 0, reverse=True)
        return runs

    def run_details(self, name: str) -> dict:
        d = self.run_dir(name)
        if not d.is_dir():
            raise ApiError(f"Run inconnu : {name}", HTTPStatus.NOT_FOUND)
        progress = read_progress(d)
        config = None
        for candidate in ("config.yaml", "config_lancement.yaml"):
            if (d / candidate).exists():
                config = yaml.safe_load((d / candidate).read_text(encoding="utf-8"))
                break
        report = d / "eval" / "rapport.md"
        log_path = d / OUTPUT_LOG if (d / OUTPUT_LOG).exists() else d / "train.log"
        return {
            "nom": name,
            "statut": self._status(name, progress),
            "actif": self._alive(name),
            "progression": progress,
            "config": config,
            "donnees": _read_json(d / "data" / "rapport.json"),
            "metriques": _read_json(d / "eval" / "metrics.json"),
            "metriques_entrainement": _read_json(d / "metrics_entrainement.json"),
            "rapport": report.read_text(encoding="utf-8") if report.exists() else None,
            "journal": tail_log(log_path),
            "chemin": str(d.resolve()),
            "checkpoints": (d / "checkpoints").is_dir() and any((d / "checkpoints").glob("checkpoint-*")),
        }

    # --- configurations -------------------------------------------------------------------------------
    def list_configs(self) -> list[str]:
        if not self.configs_dir.is_dir():
            return []
        return sorted(p.name for p in self.configs_dir.glob("*.yaml"))

    def load_config_dict(self, nom: str | None = None, run: str | None = None) -> dict:
        if run:
            path = self.run_dir(run) / "config.yaml"
            if not path.exists():
                raise ApiError(f"Pas de config.yaml dans le run {run}", HTTPStatus.NOT_FOUND)
            return load_config(path).to_dict()
        if nom:
            if nom not in self.list_configs():
                raise ApiError(f"Configuration inconnue : {nom}", HTTPStatus.NOT_FOUND)
            return load_config(self.configs_dir / nom).to_dict()
        return Config().to_dict()

    def preview(self, cfg_dict: dict) -> dict:
        """Compte les paires disponibles et simule le découpage (sans tokenizer, donc avant le filtre de longueur)."""
        from .data import load_dataset_splits

        cfg = _validated(cfg_dict)
        try:
            train, evals, report = load_dataset_splits(cfg.data, apply_limit=False)
        except (ValueError, OSError) as e:
            raise ApiError(str(e)) from e
        limit = cfg.data.train_limit
        return {
            "fichiers": report.files,
            "lues": report.read,
            "disponibles_train": len(train),
            "utilisees_train": min(limit, len(train)) if limit else len(train),
            "eval": len(evals),
            "test": len(report.test_pairs),
            "prompt_des_donnees": report.prompt_template is not None,
            "methode": report.split_method,
            "rejets": dict(report.dropped),
            "avertissements": report.warnings,
            "groupes_train": dict(Counter(p.group for p in train).most_common()),
            "groupes_eval": dict(Counter(p.group for p in evals).most_common()),
        }

    # --- lancement / arrêt ----------------------------------------------------------------------------
    def start(self, cfg_dict: dict, name: str, resume: bool = False) -> dict:
        with self._lock:
            active = self.active()
            if active and (read_progress(self.runs_dir / active) or {}).get("status") != RUNNING:
                # Run fini dont le processus se ferme encore (libération du GPU) : on lui laisse le temps.
                deadline = time.time() + 30
                while self._alive(active) and time.time() < deadline:
                    time.sleep(0.25)
                active = self.active()
            if active:
                raise ApiError(f"Un entraînement est déjà en cours ({active}) : un seul à la fois sur le GPU.",
                               HTTPStatus.CONFLICT)
            run_dir = self.run_dir(name)
            if resume:
                if not any((run_dir / "checkpoints").glob("checkpoint-*")):
                    raise ApiError(f"Aucun checkpoint à reprendre dans {name}.")
            elif run_dir.exists() and any(run_dir.iterdir()):
                raise ApiError(f"Le run « {name} » existe déjà : choisissez un autre nom (ou reprenez-le).",
                               HTTPStatus.CONFLICT)
            cfg_dict = json.loads(json.dumps(cfg_dict))  # copie
            cfg_dict.setdefault("training", {})["output_dir"] = str(run_dir)
            cfg_dict["training"]["resume_from_checkpoint"] = "last" if resume else None
            cfg = _validated(cfg_dict)
            run_dir.mkdir(parents=True, exist_ok=True)
            config_path = run_dir / "config_lancement.yaml"
            save_config(cfg, config_path)
            # État initial, remplacé par le processus d'entraînement dès son démarrage.
            (run_dir / "progress.json").write_text(json.dumps({
                "status": RUNNING, "phase": "lancement du processus", "started_at": time.time(),
                "updated_at": time.time(), "step": 0, "max_steps": None, "history": [], "error": None,
            }), encoding="utf-8")
            command = [*self.command, "train", "--config", str(config_path)]
            with open(run_dir / OUTPUT_LOG, "ab") as out:
                proc = subprocess.Popen(
                    command, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                    start_new_session=True, env={**os.environ, "PYTHONUNBUFFERED": "1"},
                )
            self._procs[name] = proc
            (run_dir / JOB_FILE).write_text(json.dumps({"pid": proc.pid, "lance_le": time.time(),
                                                        "commande": command}), encoding="utf-8")
            log.info("Entraînement « %s » lancé (pid %d)", name, proc.pid)
            return {"nom": name, "pid": proc.pid}

    def stop(self, name: str, force: bool = False) -> dict:
        run_dir = self.run_dir(name)
        if not self._alive(name):
            raise ApiError(f"Aucun entraînement en cours pour {name}.")
        if force:
            job = _read_json(run_dir / JOB_FILE) or {}
            pid = self._procs[name].pid if name in self._procs else int(job.get("pid", 0))
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError) as e:
                raise ApiError(f"Arrêt impossible : {e}") from e
            return {"arret": "forcé"}
        request_stop(run_dir)
        return {"arret": "demandé"}


def _validated(cfg_dict: dict) -> Config:
    try:
        return _build(Config, cfg_dict)
    except (TypeError, ValueError) as e:
        raise ApiError(f"Configuration invalide : {e}") from e


class _Handler(BaseHTTPRequestHandler):
    server: IhmServer
    protocol_version = "HTTP/1.1"

    # --- utilitaires ----------------------------------------------------------------------------------
    def log_message(self, fmt, *args):  # journal HTTP silencieux (le polling est fréquent)
        log.debug("%s - %s", self.address_string(), fmt % args)

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, status: int = HTTPStatus.OK) -> None:
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _error(self, message: str, status: int) -> None:
        self._json({"erreur": message}, status)

    def _authorized(self, query: dict) -> bool:
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]").lower()
        if self.server.loopback and host not in ("localhost", "127.0.0.1", "::1"):
            return False
        if self.server.token:
            given = self.headers.get(TOKEN_HEADER) or (query.get("jeton") or [""])[0]
            return secrets.compare_digest(given, self.server.token)
        return True

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length > 2_000_000:
            raise ApiError("Requête trop volumineuse")
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError as e:
            raise ApiError(f"JSON invalide : {e}") from e
        if not isinstance(data, dict):
            raise ApiError("Un objet JSON est attendu")
        return data

    # --- routes ---------------------------------------------------------------------------------------
    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if not self._authorized(query):
            return self._error("Accès refusé (hôte ou jeton invalide)", HTTPStatus.FORBIDDEN)
        jobs = self.server.jobs
        try:
            if url.path in ("/", "/index.html"):
                return self._send(HTTPStatus.OK, STATIC_PAGE.read_bytes(), "text/html; charset=utf-8")
            if url.path == "/api/etat":
                return self._json({"actif": jobs.active(), "gpu": gpu_stats(), "configs": jobs.list_configs(),
                                   "dossier_runs": str(jobs.runs_dir.resolve())})
            if url.path == "/api/config":
                nom = (query.get("nom") or [None])[0]
                run = (query.get("run") or [None])[0]
                return self._json({"config": jobs.load_config_dict(nom=nom, run=run)})
            if url.path == "/api/runs":
                return self._json({"runs": jobs.list_runs()})
            if url.path.startswith("/api/runs/"):
                return self._json(jobs.run_details(unquote(url.path[len("/api/runs/"):])))
            return self._error("Introuvable", HTTPStatus.NOT_FOUND)
        except ApiError as e:
            return self._error(str(e), e.status)
        except Exception as e:  # noqa: BLE001
            log.exception("Erreur sur %s", url.path)
            return self._error(f"Erreur interne : {e}", HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self):
        url = urlparse(self.path)
        if not self._authorized(parse_qs(url.query)):
            return self._error("Accès refusé (hôte ou jeton invalide)", HTTPStatus.FORBIDDEN)
        if self.headers.get(POST_HEADER) != "1" or "application/json" not in (self.headers.get("Content-Type") or ""):
            return self._error("Requête refusée (en-têtes manquants)", HTTPStatus.FORBIDDEN)
        jobs = self.server.jobs
        try:
            body = self._body()
            if url.path == "/api/apercu":
                return self._json(jobs.preview(body.get("config") or {}))
            if url.path == "/api/lancer":
                return self._json(jobs.start(body.get("config") or {}, str(body.get("nom", "")),
                                             bool(body.get("reprendre"))))
            if url.path == "/api/arreter":
                return self._json(jobs.stop(str(body.get("nom", "")), bool(body.get("forcer"))))
            return self._error("Introuvable", HTTPStatus.NOT_FOUND)
        except ApiError as e:
            return self._error(str(e), e.status)
        except Exception as e:  # noqa: BLE001
            log.exception("Erreur sur %s", url.path)
            return self._error(f"Erreur interne : {e}", HTTPStatus.INTERNAL_SERVER_ERROR)


class IhmServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, host: str, port: int, jobs: TrainingJobs, token: str | None = None):
        super().__init__((host, port), _Handler)
        self.jobs = jobs
        try:
            self.loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            self.loopback = host == "localhost"
        self.token = token if token is not None else (None if self.loopback else secrets.token_urlsafe(18))

    @property
    def url(self) -> str:
        host, port = self.server_address[:2]
        shown = "127.0.0.1" if self.loopback else host
        return f"http://{shown}:{port}/" + (f"?jeton={self.token}" if self.token else "")


def serve(host: str = "127.0.0.1", port: int = 7860, runs_dir: str = "entrainement/runs",
          configs_dir: str | None = None, open_browser: bool = True) -> None:
    jobs = TrainingJobs(Path(runs_dir), Path(configs_dir) if configs_dir else DEFAULT_CONFIGS_DIR)
    server = IhmServer(host, port, jobs)
    print(f"Interface d'entraînement : {server.url}")
    if not server.loopback:
        print("Attention : l'interface est accessible depuis le réseau ; ne partagez le lien (jeton) qu'avec "
              "des personnes de confiance. Préférez un tunnel SSH : ssh -L 7860:127.0.0.1:7860 <machine>")
    print(f"Runs : {jobs.runs_dir.resolve()} — Ctrl+C pour quitter (un entraînement en cours continue).")
    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(server.url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nInterface arrêtée.")
    finally:
        server.server_close()
