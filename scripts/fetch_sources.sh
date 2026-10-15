#!/usr/bin/env bash
# Récupère les sources du corpus (voir sources/CATALOGUE.md et reports/).
#
# Usage:
#   scripts/fetch_sources.sh vendored   # sources sous licence permissive, copiées dans sources/
#   scripts/fetch_sources.sh local      # sources copyleft / licence floue, copiées dans sources_local/ (non versionné)
#   scripts/fetch_sources.sh all
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

clone() { # clone <url> <dir>
  git clone --quiet --depth 1 "$1" "$WORK/$2"
}

copy_subset() { # copy_subset <repo-dir> <dest> <path>...
  local repo="$1" dest="$2"; shift 2
  mkdir -p "$dest"
  for p in "$@"; do
    if [ -e "$WORK/$repo/$p" ]; then
      mkdir -p "$dest/$(dirname "$p")"
      cp -r "$WORK/$repo/$p" "$dest/$(dirname "$p")/"
    else
      echo "  absent: $repo/$p" >&2
    fi
  done
  for l in LICENSE LICENSE.md LICENSE.txt LICENCE COPYING; do
    [ -f "$WORK/$repo/$l" ] && cp "$WORK/$repo/$l" "$dest/" || true
  done
  git -C "$WORK/$repo" rev-parse HEAD > "$dest/SOURCE_COMMIT"
}

vendored() {
  local out="$ROOT/sources"
  echo "# Catala (Apache-2.0, hors impot_revenu: CeCILL 2.1)"
  clone https://github.com/CatalaLang/catala-examples.git catala
  rm -rf "$WORK/catala/impot_revenu" "$WORK/catala/NSW_community_gaming" "$WORK/catala/polish_taxes" "$WORK/catala/us_tax_code"
  copy_subset catala "$out/regles-as-code/catala-examples" .
  rm -rf "$out/regles-as-code/catala-examples/.git" "$out/regles-as-code/catala-examples/.github" "$out/regles-as-code/catala-examples/.devcontainer"

  echo "# aplypro (MIT)"
  clone https://github.com/betagouv/aplypro.git aplypro
  copy_subset aplypro "$out/gherkin-fr/aplypro" features

  echo "# acces-cible (MIT)"
  clone https://github.com/betagouv/acces-cible.git accescible
  copy_subset accescible "$out/gherkin-fr/acces-cible" features

  echo "# oots-france (Apache-2.0)"
  clone https://github.com/numerique-gouv/oots-france.git oots
  copy_subset oots "$out/gherkin-fr/oots-france" features

  echo "# mon-entreprise (MIT) — règles Publicodes et tests"
  clone https://github.com/betagouv/mon-entreprise.git monentreprise
  copy_subset monentreprise "$out/regles-as-code/mon-entreprise" modele-social modele-ti modele-as modele-commun

  echo "# EUDI Wallet ARF (CC BY 4.0) et règles DCC (Apache-2.0)"
  clone https://github.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework.git arf
  copy_subset arf "$out/ue/eudi-arf" docs/annexes
  clone https://github.com/eu-digital-green-certificates/dgc-business-rules-testdata.git dcc
  copy_subset dcc "$out/ue/dcc-business-rules" .
  rm -rf "$out/ue/dcc-business-rules/.git"
}

local_only() {
  local out="$ROOT/sources_local"
  echo "# OpenFisca-France (AGPL-3.0) — tests YAML"
  clone https://github.com/openfisca/openfisca-france.git ofr
  copy_subset ofr "$out/openfisca-france" tests openfisca_france/tests

  echo "# potentiel (AGPL-3.0) — .feature"
  clone https://github.com/MTES-MCT/potentiel.git potentiel
  mkdir -p "$out/potentiel"
  (cd "$WORK/potentiel" && find . -name '*.feature' -print0 | xargs -0 -I{} cp --parents {} "$out/potentiel/")

  echo "# Code du travail numérique (licence à clarifier: Apache-2.0 vs MIT)"
  clone https://github.com/SocialGouv/code-du-travail-numerique.git cdtn
  copy_subset cdtn "$out/code-du-travail-numerique" packages/code-du-travail-modeles

  echo "# EN 16931 Schematron (EUPL-1.2)"
  clone https://github.com/ConnectingEurope/eInvoicing-EN16931.git en16931
  copy_subset en16931 "$out/en16931" schematron ubl cii

  echo "# aides-jeunes (AGPL-3.0)"
  clone https://github.com/betagouv/aides-jeunes.git aj
  copy_subset aj "$out/aides-jeunes" data
}

case "${1:-all}" in
  vendored) vendored ;;
  local) local_only ;;
  all) vendored; local_only ;;
  *) echo "usage: $0 {vendored|local|all}" >&2; exit 2 ;;
esac
