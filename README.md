# Freemap Tracking pre Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Komponent (custom component) pre Home Assistant, ktorý integruje sledovanie polohy zo služby [Freemap.sk](https://www.freemap.sk).

## Funkcie

- `device_tracker` entity pre sledované zariadenia
- `sensor` entity s doplňujúcimi údajmi
- Pripojenie cez WebSocket (`cloud_push`) s automatickým opätovným pripojením
- Konfigurácia cez UI (auth token pre vlastné zariadenia alebo verejné tokeny)

## Inštalácia

### HACS (odporúčané)

1. V HACS kliknite na (⋮) → **Vlastné úložiská**.
2. Pridajte URL adresu tohto repozitára ako typ **Integrácia**.
3. Vyhľadajte **Freemap Tracking** a nainštalujte ho.
4. Reštartujte Home Assistant.

### Manuálne

1. Skopírujte priečinok `custom_components/freemap` do `<config>/custom_components/`.
2. Reštartujte Home Assistant.

## Konfigurácia

Po reštarte HA pridajte integráciu cez **Nastavenia → Zariadenia a služby → Integrácia → Pridať integráciu → Freemap Tracking** a zadajte:

- **Auth token** – pre vlastné zariadenia (podľa uvedeného návodu) a/alebo
- **Verejné tokeny** – čiarkou oddelený zoznam verejných tokenov sledovaných zariadení.

## Licencia

MIT
