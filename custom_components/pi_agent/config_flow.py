"""Config flow for Raspberry Pi Agent integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class PiAgentConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Raspberry Pi Agent."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.host: str | None = None
        self.port: int | None = None
        self.mac: str | None = None
        self.hostname: str | None = None

    async def async_step_zeroconf(
        self, discovery_info: dict
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        
        # 從 mDNS 廣播中萃取資料
        self.host = discovery_info.host
        self.port = discovery_info.port
        self.hostname = discovery_info.hostname.removesuffix(".local.")
        
        # 抓取我們在 Pi 端放在 properties 裡的 MAC address
        properties = discovery_info.properties
        self.mac = properties.get("mac_address")

        if not self.mac:
            return self.async_abort(reason="no_mac")

        # 設定 Unique ID (MAC 地址最適合)，這樣就不會重複發現同一台樹莓派
        await self.async_set_unique_id(self.mac)
        self._abort_if_unique_id_configured(updates={"host": self.host, "port": self.port})

        # 設定在「發現新裝置」區塊顯示的名字
        self.context.update({"title_placeholders": {"name": self.hostname}})

        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None:
            # 當使用者按下「送出」按鈕
            # 抓取他們在輸入框填寫的裝置名稱，當作這台設備在 HA 裡的名稱
            title = user_input.get("name", self.hostname)
            
            return self.async_create_entry(
                title=title,
                data={
                    "host": self.host,
                    "port": self.port,
                    "mac": self.mac,
                },
            )

        # 定義跳出的精靈畫面表單，並將「樹莓派主機名稱」作為預設值填入
        data_schema = vol.Schema(
            {
                vol.Required("name", default=self.hostname): str,
            }
        )

        # 顯示加入精靈
        return self.async_show_form(
            step_id="discovery_confirm",
            data_schema=data_schema,
            description_placeholders={"name": self.hostname},
        )
