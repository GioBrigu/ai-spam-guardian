"""
Avvia lo scheduler e lo mantiene in esecuzione finché non premi Ctrl+C.
Finché non esiste una GUI, questo script è il modo per far girare l'app in background.

Uso (dalla root del progetto):
    uv run scripts/avvia_scheduler.py
"""

import time

from spam_guardian import config
from spam_guardian.core.scheduler import crea_scheduler

scheduler = crea_scheduler()
scheduler.start()

print(f'Scheduler avviato: pipeline ogni {config.INTERVALLO_MINUTI} minuti. Premi Ctrl+C per fermare.')

try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
    print('Scheduler fermato.')