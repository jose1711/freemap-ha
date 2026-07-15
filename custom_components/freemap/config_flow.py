from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_URL, CONF_AUTH_TOKEN, CONF_PUBLIC_TOKENS, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_AUTH_TOKEN, default=""): str,
        vol.Optional(CONF_PUBLIC_TOKENS, default=""): str,
    }
)


class FreemapConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            auth_token = user_input[CONF_AUTH_TOKEN].strip() or None
            raw_tokens = user_input[CONF_PUBLIC_TOKENS]
            public_tokens = [t.strip() for t in raw_tokens.split(",") if t.strip()]

            if not auth_token and not public_tokens:
                errors["base"] = "no_credentials"
            else:
                if auth_token:
                    error = await self._validate_token(auth_token)
                    if error:
                        errors["base"] = error

                if not errors:
                    await self.async_set_unique_id(
                        auth_token or ",".join(sorted(public_tokens))
                    )
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=_build_title(auth_token, public_tokens),
                        data={
                            CONF_AUTH_TOKEN: auth_token,
                            CONF_PUBLIC_TOKENS: public_tokens,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
            description_placeholders={
                "token_help": (
                    "Auth token nájdete v prehliadači: "
                    "Prihláste sa na Freemap.sk, otvorte Nastavenia → Ďalšie nástroje → "
                    "Nástroje pre vývojárov webu → Sieť. Do riadka pre URL adresu vložte "
                    "https://www.freemap.sk/?track=0. Prepnite sa do panela WS, kde nájdete "
                    "authToken ako súčasť požiadavky."
                )
            },
        )

    async def _validate_token(self, token: str) -> str | None:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                f"{API_URL}/tracking/devices",
                headers={"Authorization": f"Bearer {token}"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    return "invalid_auth"
                if resp.status != 200:
                    return "cannot_connect"
        except aiohttp.ClientError:
            return "cannot_connect"
        return None


def _build_title(auth_token: str | None, public_tokens: list[str]) -> str:
    parts = []
    if auth_token:
        parts.append("Freemap (vlastné zariadenia)")
    if public_tokens:
        parts.append(", ".join(public_tokens))
    return " + ".join(parts) if parts else "Freemap"
