#!/usr/bin/env bash
# Télécharge des codes du jeu AgentPublic/legi (Licence Ouverte 2.0) vers le dossier donné.
# Usage: telecharger_legi.sh <dossier>
set -u
D="$1"; mkdir -p "$D"
CODES="legi_code_de_la_securite_sociale legi_code_du_travail legi_code_de_l_action_sociale_et_des_familles
legi_code_de_la_construction_et_de_l_habitation legi_code_de_l_education legi_code_de_la_route
legi_code_de_la_sante_publique legi_code_de_la_consommation legi_code_de_l_urbanisme
legi_code_des_pensions_civiles_et_militaires_de_retraite legi_code_general_des_impots
legi_livre_des_procedures_fiscales legi_code_de_l_entree_et_du_sejour_des_etrangers_et_du_droit_d_asile
legi_code_de_commerce legi_code_des_assurances legi_code_rural_et_de_la_peche_maritime
legi_code_de_l_environnement legi_code_de_la_commande_publique"
for c in $CODES; do
  [ -s "$D/$c.parquet" ] && continue
  for essai in 1 2 3; do
    curl -sS -m 900 -L -f -o "$D/$c.parquet.tmp" "https://huggingface.co/datasets/AgentPublic/legi/resolve/main/data/legi-latest/$c/${c}_part_0.parquet" && mv "$D/$c.parquet.tmp" "$D/$c.parquet" && break
    sleep 5
  done
  [ -s "$D/$c.parquet" ] && echo "ok $c" || echo "echec $c"
done
echo FIN
