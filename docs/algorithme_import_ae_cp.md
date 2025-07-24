# 🧾 Algorithme d’import des fichiers AE/CP

## 1. 📥 Import initial (année N, région R)

### 🔄 Nettoyage préalable :
- ❌ Suppression des CP existants pour l’année **N** et la région **R**.
- ❌ Suppression des AE **sans DP associée** pour l’année **N** et la région **R**.

---

### 📑 Parsing des fichiers

#### Fichier **AE** :
- Chaque ligne est stockée dans une **map `ae_list`**, avec comme **clé** :
  ```
  regional_{source_region}_{annee}_{n_ej}_{n_poste_ej}
  ```
- ➕ Permet de regrouper plusieurs AE pour un même `(n_ej, n_poste_ej)`.

#### Fichier **CP** :
- Pour chaque ligne CP :
  - 🔎 Vérifie s’il existe un AE correspondant.
    - ✅ **Oui** → associé dans `ae_list` sous la bonne clé.
    - ❌ **Non** → stocké dans `cp_list` (orphelins).

---

### 📦 Résultat du parsing

#### Map `ae_list`
```json
{
  "regional_176_2024_1512615774_1": {
    "ae": [...],
    "cp": [...]
  },
  ...
}
```

#### Map `cp_list`
```json
{
  "cp_orphelin_1": {...},
  ...
}
```

---

## 2. ⚙️ Traitement asynchrone

- 🧵 Découpe de `ae_list` en paquets de 10 → envois aux tâches `import_ae`.
- 🧵 Découpe de `cp_list` en paquets de 10 → envois aux tâches `import_cp`.

---

## 3. 🔁 Traitement ligne par ligne des AE (`import_ae`)

Pour chaque AE :

### 🔍 Vérification en base :
- Recherche par `n_ej`, `n_poste_ej`, et `source` (Région ou Nation).

---

### 🧱 Cas 1 : AE inexistant
- Création de l’AE :
  - Appel API SIRET
  - Insertion des référentiels
  - Insertion AE en base

---

### 🔧 Cas 2 : AE déjà existant
- Mise à jour des données :
  - Référentiels, exercice comptable, etc.
- 📊 Récupération de l’historique des montants par année comptable.

---

### 📐 Règles de traitement du **montant engagé**

| Nouveau Montant | Historique              | Action                                                                 |
|------------------|--------------------------|------------------------------------------------------------------------|
| **> 0**          | Aucun montant positif    | ➕ Ajouter ou mettre à jour l’année N                                  |
| **> 0**          | Montant positif existant | ✅ Garder uniquement le plus récent (par année comptable)              |
| **<= 0**         | Montant sur même année   | 📝 Mise à jour                                                        |
| **<= 0**         | Aucun montant existant   | ➕ Ajout du montant négatif sur l’année N                              |
| **== ancien**    | Montant déjà présent     | ✅ Pas de mise à jour                                                  |

---

## 📌 Exemple concret

#### Lignes d’entrée (même EJ/poste) avec deux montants positifs sur la même année dans le même fichier :

```plaintext
176;0176-06-07;...;1512615774;...;1;...;62456.15
176;0176-06-09;...;1512615774;...;1;...;6820.7
```

#### 🎯 Résultat :
- Deux AE sont regroupés.
- Le montant le plus récent (6820.7) est conservé selon les règles métier.

🟢 **Montant final stocké en base : 6820.7**


#### Lignes d’entrée (même EJ/poste) avec un  montant positif et un montant négatif sur la même année  :
 
```plaintext
107;0107-01;...;1511095142;...;1;...;-2225.07
107;0107-01;...;1511095142;...;1;...;2394.18
```

#### 🎯 Résultat :
- Deux AE sont regroupés.
- les deux montants sont insérés sur l'année 2025

🟢 **Montant final stocké en base : -2225.07 et 2394.18**
