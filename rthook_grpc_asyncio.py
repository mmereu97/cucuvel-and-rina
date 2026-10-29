# rthook_grpc_asyncio.py
# Acest hook rulează înainte de main_app.py pentru a preveni un conflict
# de inițializare între grpcio și asyncio pe Windows în mediul PyInstaller.

import sys
import asyncio

# Forțăm politica de event loop pentru Windows înainte ca grpc să o poată strica.
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())