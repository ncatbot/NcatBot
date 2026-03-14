import sys

import napcat

sys.modules[__name__] = napcat

NapcatAdapter = napcat.NapCatClient
