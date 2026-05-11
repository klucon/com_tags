# com_tags

Centrální tagovací systém pro obsah a další rozšíření.

## Metadata

| Pole | Hodnota |
| :--- | :--- |
| Typ | `component` |
| Verze | `0.1.9` |
| Vendor | `klucon` |
| Extension ID | `klucon/com_tags` |
| Kategorie | `content` |
| Licence | MIT |
| Core minimum | `0.1.0` |
| Python | `>=3.12` |
| Entry point | `src.components.com_tags` |
| Admin URL | `/admin/com_tags` |

## Účel

Tagy je marketplace rozšíření pro KLUCON CMS. Balíček je určený pro instalaci přes `/admin/marketplace` a musí projít validací manifestu, checksumu a podpisu.

## Struktura

```text
src/**/com_tags/
├── manifest.json
├── __init__.py
├── i18n/
└── ...
```

Manifest používá schema `1.0`, deklaruje typ `component`, kompatibilitu s core, i18n doménu `com_tags` a bezpečnostní capabilities. Implementace obsahuje admin routes podle manifestu.

## Balíčkování

Release ZIP se staví z `src/**/com_tags/manifest.json` pomocí GitHub Actions workflow `.github/workflows/release-package.yml`. Do balíčku nepatří cache, `.git`, lokální ZIP artefakty ani dočasné soubory.

## Instalace

1. Publikuj ZIP a metadata do marketplace serveru.
2. V CMS otevři `/admin/marketplace`.
3. Vyber `com_tags` a instaluj verzi `0.1.9`.
4. Po instalaci ověř záznam v příslušné tabulce `installed_*`.

## Poznámky k verzi

Aktualizace dokumentace a rebuild balíčku pro GitHub distribuci.
