from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant

from .const import API_URL, CONF_AUTH_TOKEN, CONF_PUBLIC_TOKENS, PING_INTERVAL_MS, RECONNECT_DELAY, WS_URL

_LOGGER = logging.getLogger(__name__)


class FreemapCoordinator:
    """Manages WebSocket connection to Freemap and distributes tracking updates."""

    def __init__(self, hass: HomeAssistant, entry_data: dict) -> None:
        self.hass = hass
        self.auth_token: str | None = entry_data.get(CONF_AUTH_TOKEN)
        self.public_tokens: list[str] = entry_data.get(CONF_PUBLIC_TOKENS, [])

        # key is int (deviceId) for owned devices, str (token) for public ones
        self.device_names: dict[Any, str] = {}
        self.latest_data: dict[Any, dict] = {}
        self._callbacks: dict[Any, list[Callable]] = {}

        self._session: aiohttp.ClientSession | None = None
        self._ws_task: asyncio.Task | None = None
        self._running = False
        # maps pending subscribe msg id -> key
        self._pending: dict[int | str, Any] = {}
        self._msg_counter = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def async_start(self) -> None:
        self._running = True
        self._session = aiohttp.ClientSession()

        if self.auth_token:
            await self._fetch_owned_devices()

        for token in self.public_tokens:
            if token not in self.device_names:
                self.device_names[token] = token

        self._ws_task = self.hass.loop.create_task(self._ws_loop())

    async def async_stop(self) -> None:
        self._running = False
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        if self._session:
            await self._session.close()
            self._session = None

    def tracked_keys(self) -> list[Any]:
        return list(self.device_names.keys())

    def register_callback(self, key: Any, callback: Callable) -> None:
        self._callbacks.setdefault(key, []).append(callback)

    def unregister_callback(self, key: Any, callback: Callable) -> None:
        callbacks = self._callbacks.get(key, [])
        if callback in callbacks:
            callbacks.remove(callback)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _fetch_owned_devices(self) -> None:
        assert self._session is not None
        try:
            async with self._session.get(
                f"{API_URL}/tracking/devices",
                headers={"Authorization": f"Bearer {self.auth_token}"},
            ) as resp:
                if resp.status == 200:
                    devices: list[dict] = await resp.json()
                    for dev in devices:
                        self.device_names[dev["id"]] = dev["name"]
                elif resp.status == 401:
                    _LOGGER.error("Freemap: invalid auth token")
                else:
                    _LOGGER.error("Freemap: failed to fetch devices (%s)", resp.status)
        except aiohttp.ClientError as exc:
            _LOGGER.error("Freemap: error fetching devices: %s", exc)

    def _next_id(self) -> int:
        self._msg_counter += 1
        return self._msg_counter

    async def _ws_loop(self) -> None:
        assert self._session is not None
        while self._running:
            try:
                ws_url = f"{WS_URL}?pingInterval={PING_INTERVAL_MS}"
                if self.auth_token:
                    ws_url += f"&authToken={self.auth_token}"

                async with self._session.ws_connect(ws_url, heartbeat=30) as ws:
                    _LOGGER.info("Freemap: WebSocket connected")
                    self._pending.clear()
                    self._msg_counter = 0

                    await self._subscribe_all(ws)

                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            if msg.data == "ping":
                                await ws.send_str("pong")
                                continue
                            try:
                                self._dispatch(json.loads(msg.data))
                            except json.JSONDecodeError:
                                pass
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break

                _LOGGER.warning("Freemap: WebSocket disconnected")

            except asyncio.CancelledError:
                return
            except Exception as exc:
                _LOGGER.error("Freemap: WebSocket error: %s", exc)

            if self._running:
                _LOGGER.info("Freemap: reconnecting in %ss", RECONNECT_DELAY)
                await asyncio.sleep(RECONNECT_DELAY)

    async def _subscribe_all(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        for key, name in self.device_names.items():
            msg_id = self._next_id()
            if isinstance(key, int):
                params: dict = {"deviceId": key, "maxCount": 1}
            else:
                params = {"token": key, "maxCount": 1}
            self._pending[msg_id] = key
            await ws.send_json({
                "jsonrpc": "2.0",
                "method": "tracking.subscribe",
                "id": msg_id,
                "params": params,
            })
            _LOGGER.debug("Freemap: subscribed to %s (%s)", name, key)

    def _dispatch(self, data: dict) -> None:
        method = data.get("method")

        if method == "tracking.addPoint":
            params = data.get("params", {})
            key = params.get("deviceId") or params.get("token")
            if key is not None:
                self._update(key, params)

        elif "result" in data and "id" in data:
            # Initial response to tracking.subscribe
            key = self._pending.pop(data["id"], None)
            if key is not None:
                points: list[dict] = data["result"] or []
                if points:
                    self._update(key, points[-1])

        elif "error" in data:
            _LOGGER.warning("Freemap: RPC error: %s", data["error"])

    def _update(self, key: Any, point: dict) -> None:
        self.latest_data[key] = point
        for cb in list(self._callbacks.get(key, [])):
            cb()
