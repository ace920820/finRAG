from typing import Union

from app.core.config import get_settings
from app.core.providers.rerank import BailianTextProvider, MockTextProvider


def build_text_provider() -> Union[MockTextProvider, BailianTextProvider]:
    settings = get_settings()
    if settings.text_provider == "bailian":
        return BailianTextProvider()
    return MockTextProvider()
