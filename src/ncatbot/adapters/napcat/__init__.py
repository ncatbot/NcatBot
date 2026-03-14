import napcat.exceptions
import napcat.matcher
import napcat.types
from napcat import NapCatClient, __version__

from ..base import BaseAdapter


class NapcatAdapter(NapCatClient, BaseAdapter):
    @property
    def adapter_name(self) -> str:
        return "Ncatbot.NapcatAdapter"

    @property
    def adapter_version(self) -> str:
        return __version__

    @property
    def platform_name(self) -> str:
        return "qq"


exceptions = napcat.exceptions
types = napcat.types
matcher = napcat.matcher

__all__ = ["NapcatAdapter", "exceptions", "types", "matcher"]
