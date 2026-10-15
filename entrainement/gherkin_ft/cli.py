"""Ligne de commande : gherkin-ft <commande> (ou python -m gherkin_ft <commande>)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .config import DataConfig, load_config


def _add_config_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--config", "-c", help="Fichier YAML de configuration")
    p.add_argument("--set", "-s", action="append", default=[], metavar="CLÉ=VALEUR",
                   help="Surcharge, ex. --set training.learning_rate=2e-4 (répétable)")


def cmd_check_env(args) -> int:
    from .env import check_environment

    return 0 if check_environment(test_4bit=not args.no_4bit) else 1


def cmd_prepare(args) -> int:
    from .modeling import load_tokenizer
    from .train import prepare_data

    cfg = load_config(args.config, args.set)
    out = Path(cfg.training.output_dir)
    tokenizer = load_tokenizer(cfg.model.name_or_path, cfg.model.revision)
    prepare_data(cfg, tokenizer, out)
    print((out / "data" / "rapport.json").read_text(encoding="utf-8"))
    return 0


def cmd_train(args) -> int:
    from .train import run_training

    cfg = load_config(args.config, args.set)
    adapter = run_training(cfg)
    print(f"Adaptateur : {adapter}")
    return 0


def _load_eval_pairs(path: str, expected_language: str):
    from .data import DataReport, Pair, load_pairs, read_records

    records = read_records(Path(path))
    if records and {"id", "specification", "gherkin", "group"} <= set(records[0]):
        fields = {"id", "specification", "gherkin", "group", "split", "source_file", "meta"}
        return [Pair(**{k: v for k, v in r.items() if k in fields}) for r in records]
    cfg = DataConfig(require_valid_gherkin=False, expected_language=expected_language)
    return load_pairs([path], cfg, DataReport())


def cmd_evaluate(args) -> int:
    from .evaluation import evaluate_pairs
    from .generation import GenerationParams
    from .modeling import load_for_inference

    cfg = load_config(args.config, args.set)
    # Sans --model ni --adapter : modèle de base de la configuration (mesure de référence avant affinage).
    base = args.model or (None if args.adapter else cfg.model.name_or_path)
    model, tokenizer, info = load_for_inference(base, args.adapter, load_in_4bit=args.load_in_4bit)
    data = args.data
    if data is None and args.adapter and Path(args.adapter).parent.joinpath("data", "eval.jsonl").exists():
        data = str(Path(args.adapter).parent / "data" / "eval.jsonl")
    if data is None:
        print("Indiquez --data (fichier de paires) : aucun eval.jsonl trouvé à côté de l'adaptateur.", file=sys.stderr)
        return 2
    lang = info.get("expected_language", cfg.data.expected_language)
    pairs = _load_eval_pairs(data, lang)
    e = cfg.eval
    max_samples = args.max_samples or e.max_samples
    if max_samples:
        pairs = pairs[:max_samples]
    params = GenerationParams(
        max_new_tokens=args.max_new_tokens or e.max_new_tokens,
        batch_size=args.batch_size or e.batch_size,
        do_sample=e.do_sample, temperature=e.temperature, top_p=e.top_p, repetition_penalty=e.repetition_penalty,
    )
    # Le prompt de l'adaptateur prime : le modèle doit voir le prompt de son entraînement.
    system_prompt = info.get("system_prompt", cfg.prompt.system_prompt)
    user_template = info.get("user_template", cfg.prompt.user_template)
    out = args.out or (str(Path(args.adapter).parent / "eval") if args.adapter else "entrainement/runs/eval-base")
    label = args.label or ("affiné" if args.adapter else "base")
    metrics = evaluate_pairs(model, tokenizer, pairs, system_prompt, user_template, params, lang, out, label)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


def cmd_compare(args) -> int:
    from .evaluation import compare

    print(compare(args.metrics))
    return 0


def cmd_merge(args) -> int:
    from .merge import merge_adapter

    merge_adapter(args.adapter, args.out, base=args.model, device=args.device)
    return 0


def cmd_generate(args) -> int:
    from .config import PromptConfig
    from .generation import GenerationParams, generate
    from .modeling import load_for_inference
    from .prompts import build_prompt_messages
    from .quality import analyze_gherkin, extract_gherkin, quality_score

    if args.spec:
        spec = args.spec
    elif args.spec_file:
        spec = Path(args.spec_file).read_text(encoding="utf-8")
    else:
        spec = sys.stdin.read()
    model, tokenizer, info = load_for_inference(args.model, args.adapter, load_in_4bit=args.load_in_4bit)
    defaults = PromptConfig()
    messages = build_prompt_messages(args.id, spec, info.get("system_prompt", defaults.system_prompt),
                                     info.get("user_template", defaults.user_template))
    lang = info.get("expected_language", "fr")
    best = None
    for attempt in range(args.retries + 1):
        # 1er essai glouton, puis échantillonnage pour varier si la sortie est invalide.
        params = GenerationParams(max_new_tokens=args.max_new_tokens, batch_size=1, do_sample=attempt > 0,
                                  temperature=args.temperature)
        text, finished = generate(model, tokenizer, [messages], params)[0]
        text = extract_gherkin(text, lang)
        a = analyze_gherkin(text, args.id, spec, lang)
        score = quality_score(a, args.id)
        if best is None or score > best[1]:
            best = (text, score, a, finished)
        if a.syntax_ok and a.language_ok and finished:
            break
        reason = a.error or (f"langue {a.language}" if a.syntax_ok and not a.language_ok else "") or "tronquée"
        print(f"Essai {attempt + 1} : sortie invalide ({reason})", file=sys.stderr)
    text, score, a, finished = best
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    print(f"\n# score qualité {score} ; syntaxe {'ok' if a.syntax_ok else 'KO'} ; scénarios {a.n_scenarios} ; "
          f"types {a.case_types}", file=sys.stderr)
    return 0 if a.syntax_ok else 1


def cmd_ihm(args) -> int:
    from .ihm import serve

    serve(host=args.host, port=args.port, runs_dir=args.runs_dir, configs_dir=args.configs_dir,
          open_browser=not args.no_browser)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gherkin-ft", description="Affinage de Ministral 3 3B pour écrire du Gherkin")
    parser.add_argument("--verbose", "-v", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check-env", help="Vérifie GPU, CUDA et bibliothèques")
    p.add_argument("--no-4bit", action="store_true", help="Ne pas tester bitsandbytes")
    p.set_defaults(func=cmd_check_env)

    p = sub.add_parser("prepare", help="Prépare et découpe les données sans entraîner (statistiques, rejets)")
    _add_config_args(p)
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("train", help="Entraîne l'adaptateur LoRA / QLoRA")
    _add_config_args(p)
    p.set_defaults(func=cmd_train)

    for name, func, helptext in (
        ("evaluate", cmd_evaluate, "Génère sur le jeu d'évaluation et mesure la qualité"),
        ("generate", cmd_generate, "Écrit le Gherkin d'une spécification"),
    ):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("--adapter", "-a", help="Dossier de l'adaptateur (runs/<nom>/adapter)")
        p.add_argument("--model", "-m", help="Modèle de base ou fusionné (par défaut : celui de l'adaptateur)")
        p.add_argument("--load-in-4bit", action="store_true", help="Charger le modèle en 4 bits")
        p.add_argument("--max-new-tokens", type=int, default=None if name == "evaluate" else 2048)
        p.set_defaults(func=func)
        if name == "evaluate":
            _add_config_args(p)
            p.add_argument("--data", "-d", help="Paires à évaluer (défaut : data/eval.jsonl du run)")
            p.add_argument("--out", "-o", help="Dossier de sortie")
            p.add_argument("--label", help="Nom affiché dans les rapports")
            p.add_argument("--max-samples", type=int)
            p.add_argument("--batch-size", type=int)
        else:
            p.add_argument("--spec", help="Texte de la spécification")
            p.add_argument("--spec-file", "-f", help="Fichier de la spécification (défaut : entrée standard)")
            p.add_argument("--id", help="Identifiant de la règle, ex. RG-42")
            p.add_argument("--out", "-o", help="Fichier .feature de sortie (défaut : sortie standard)")
            p.add_argument("--retries", type=int, default=2, help="Nouveaux essais si la sortie est invalide")
            p.add_argument("--temperature", type=float, default=0.3, help="Température des nouveaux essais")

    p = sub.add_parser("ihm", help="Interface web locale : paramètres, lancement et suivi des entraînements")
    p.add_argument("--host", default="127.0.0.1", help="Adresse d'écoute (défaut : 127.0.0.1, machine locale)")
    p.add_argument("--port", type=int, default=7860)
    p.add_argument("--runs-dir", default="entrainement/runs", help="Dossier des runs")
    p.add_argument("--configs-dir", help="Dossier des configurations de départ (défaut : entrainement/configs)")
    p.add_argument("--no-browser", action="store_true", help="Ne pas ouvrir le navigateur")
    p.set_defaults(func=cmd_ihm)

    p = sub.add_parser("compare", help="Compare plusieurs metrics.json")
    p.add_argument("metrics", nargs="+")
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("merge", help="Fusionne l'adaptateur dans le modèle de base (bf16)")
    p.add_argument("--adapter", "-a", required=True)
    p.add_argument("--out", "-o", required=True)
    p.add_argument("--model", "-m", help="Modèle de base (par défaut : celui de l'adaptateur)")
    p.add_argument("--device", choices=["auto", "cpu"], default="auto")
    p.set_defaults(func=cmd_merge)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    if not args.verbose:
        for noisy in ("httpx", "httpx2", "huggingface_hub", "urllib3"):
            logging.getLogger(noisy).setLevel(logging.WARNING)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
