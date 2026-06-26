"""MiMo text provider — OpenAI-compatible LLM client."""

import logging
from typing import Optional
from openai import OpenAI

from .. import TextProvider
from ...config_model import MiMoConfig

logger = logging.getLogger(__name__)


class MiMoTextProvider(TextProvider):
    """OpenAI-compatible LLM client via MiMo."""

    def __init__(self, config: MiMoConfig):
        self._api_key = config.api_key
        self._base_url = config.base_url
        self._model = config.model

    def create_client(self) -> tuple[Optional[OpenAI], Optional[str]]:
        client = OpenAI(api_key=self._api_key, base_url=self._base_url) if self._api_key else None
        return client, self._model

    @property
    def model(self) -> Optional[str]:
        return self._model
