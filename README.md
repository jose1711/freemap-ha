# Freemap Tracking pre Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Custom komponent pre Home Assistant, ktorý integruje sledovanie polohy zo služby [Freemap.sk](https://www.freemap.sk).

## Funkcie

- `device_tracker` entity pre sledované zariadenia
- `sensor` entity s doplňujúcimi údajmi
- Pripojenie cez WebSocket (`cloud_push`) s automatickým reconnectom
- Konfigurácia cez UI (auth token pre vlastné zariadenia alebo verejné tokeny)

## Inštalácia

### HACS (odporúčané)

1. V HACS otvorte **Integrations** → menu (⋮) → **Custom repositories**.
2. Pridajte URL tohto repozitára ako typ **Integration**.
3. Vyhľadajte **Freemap Tracking** a nainštalujte.
4. Reštartujte Home Assistant.

### Manuálne

1. Skopírujte priečinok `custom_components/freemap` do `<config>/custom_components/`.
2. Reštartujte Home Assistant.

## Konfigurácia

Po reštarte pridajte integráciu cez **Nastavenia → Zariadenia a služby → Pridať integráciu → Freemap Tracking** a zadajte:

- **Auth token** – pre vlastné zariadenia,
- a/alebo **Verejné tokeny** – čiarkou oddelený zoznam verejných tokenov sledovaných zariadení.

## Licencia

MIT
