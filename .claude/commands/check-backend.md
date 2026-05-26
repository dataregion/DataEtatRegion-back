---
description: Analyse statique locale (ruff format, ruff check, pyright, importlinter) sur les sous-projets modifiés ou un scope donné. Ne lance PAS les tests.
argument-hint: "[<sous-projet> | all]   (ex: apis, app, batches, grist-plugins, services, models, gristcli, supersetcli, tests_e2e)"
---

# /check-backend — analyse statique locale

Reproduit les étapes d'**analyse statique** de `.gitlab-templates/analyze.gitlab-ci.yml`. Les tests (`pytest`) sont volontairement exclus — les lancer manuellement par sous-projet via `pytest`.

## Sélection du scope

Argument: `$ARGUMENTS`

- Si vide → détecte les sous-projets modifiés:
  ```bash
  BASE=$(git merge-base HEAD main)
  git diff --name-only "$BASE"..HEAD | awk -F/ '{print $1}' | sort -u
  ```
  Garde uniquement les dossiers présents dans la liste valide : `app apis batches grist-plugins services models gristcli supersetcli tests_e2e`.
- Si `all` → scan tous les sous-projets ci-dessus.
- Sinon → scope = sous-projet explicite (vérifier qu'il est dans la liste).

Si la sélection est vide, afficher : `Aucun sous-projet modifié — relance avec all ou un nom explicite.`

## Étapes par sous-projet

Pour chaque `<dir>` du scope:

1. **ruff format**
   ```bash
   ruff format --check <dir>
   ```
2. **ruff check**
   ```bash
   ruff check <dir>
   ```
3. **pyright** (depuis le venv du sous-projet)
   ```bash
   cd <dir> && source .venv/bin/activate && pyright . && deactivate && cd ..
   ```
4. **importlinter** (uniquement si `<dir>` ∈ `app apis batches` ET `<dir>/.importlinter.toml` existe)
   ```bash
   cd <dir> && source .venv/bin/activate && lint-imports --config .importlinter.toml --no-cache && deactivate && cd ..
   ```

## Rapport final

Pour chaque sous-projet, table:

```
<dir>  ruff-fmt ✅  ruff-check ❌  pyright ✅  importlinter —
```

Pour chaque ❌, joindre les 10 premières lignes d'erreur.

Code de sortie: 0 si tout ✅, 1 sinon.

## Notes

- Active le venv local du sous-projet, ne pas réutiliser un venv parent.
- En cas de venv absent, signaler et skip ce sous-projet (ne pas faire échouer le run global).
- Ne pas modifier le code (pas d'autofix). Pour autofix: `ruff format <dir>` / `ruff check --fix <dir>` manuellement.
