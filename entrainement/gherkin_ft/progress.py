"""Suivi de l'avancement d'un run : `progress.json` (lu par l'interface) et arrêt propre via un fichier `STOP`.

Le fichier est réécrit de façon atomique (fichier temporaire puis renommage) : un lecteur ne voit jamais
un JSON à moitié écrit.
"""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path

PROGRESS_FILE = "progress.json"
STOP_FILE = "STOP"

# Statuts finaux d'un run.
DONE, ERROR, STOPPED, RUNNING = "terminé", "erreur", "arrêté", "en cours"


def _clean(logs: dict) -> dict:
    out = {}
    for k, v in logs.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)) or (isinstance(v, float) and not math.isfinite(v)):
            continue
        out[k] = round(v, 6) if isinstance(v, float) else v
    return out


class ProgressWriter:
    def __init__(self, run_dir: str | Path, min_interval: float = 2.0):
        self.path = Path(run_dir) / PROGRESS_FILE
        self.stop_path = Path(run_dir) / STOP_FILE
        self.min_interval = min_interval
        self._last_write = 0.0
        self.data: dict = {
            "status": RUNNING,
            "phase": "démarrage",
            "started_at": time.time(),
            "updated_at": time.time(),
            "pid": os.getpid(),
            "step": 0,
            "max_steps": None,
            "epoch": 0.0,
            "history": [],
            "error": None,
        }
        if self.stop_path.exists():  # demande d'arrêt d'un lancement précédent
            self.stop_path.unlink()
        self.write(force=True)

    def write(self, force: bool = False) -> None:
        now = time.time()
        if not force and now - self._last_write < self.min_interval:
            return
        self.data["updated_at"] = now
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)
        self._last_write = now

    def update(self, force: bool = True, **fields) -> None:
        self.data.update(fields)
        self.write(force=force)

    def phase(self, name: str) -> None:
        self.update(phase=name)

    def finish(self, status: str, error: str | None = None, **fields) -> None:
        self.update(status=status, phase=status, error=error, finished_at=time.time(), **fields)

    def stop_requested(self) -> bool:
        return self.stop_path.exists()


def read_progress(run_dir: str | Path) -> dict | None:
    path = Path(run_dir) / PROGRESS_FILE
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def request_stop(run_dir: str | Path) -> None:
    Path(run_dir, STOP_FILE).touch()


def make_callback(progress: ProgressWriter):
    """TrainerCallback qui alimente `progress.json` et applique les demandes d'arrêt."""
    from transformers import TrainerCallback

    class ProgressCallback(TrainerCallback):
        def __init__(self):
            self.stopped = False
            self._train_start = None
            self._start_step = 0

        def on_train_begin(self, args, state, control, **kwargs):
            self._train_start = time.time()
            self._start_step = state.global_step  # > 0 en cas de reprise
            # En reprise, l'historique vient du checkpoint.
            history = [{**_clean(h), "step": h.get("step", 0)} for h in state.log_history]
            progress.update(phase="entraînement", step=state.global_step, max_steps=state.max_steps,
                            num_train_epochs=state.num_train_epochs, history=history, train_started_at=time.time())

        def _timing(self, state) -> dict:
            done = state.global_step - self._start_step
            if not done or not self._train_start:
                return {}
            per_step = (time.time() - self._train_start) / done
            return {"seconds_per_step": round(per_step, 3),
                    "eta_seconds": round(per_step * max(0, state.max_steps - state.global_step))}

        def on_step_end(self, args, state, control, **kwargs):
            progress.data.update(step=state.global_step, epoch=round(state.epoch or 0, 4), **self._timing(state))
            progress.write()
            if progress.stop_requested() and not self.stopped:
                self.stopped = True
                control.should_training_stop = True
                progress.update(phase="arrêt demandé : fin du pas en cours")
            return control

        def on_log(self, args, state, control, logs=None, **kwargs):
            entry = _clean(logs or {})
            if entry:
                entry["step"] = state.global_step
                progress.data["history"].append(entry)
                progress.write(force=True)

    return ProgressCallback()
