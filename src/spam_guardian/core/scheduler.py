"""
Configura lo scheduler che esegue la pipeline a intervalli regolari.
"""

from apscheduler.schedulers.background import BackgroundScheduler

from .. import config
from .pipeline import esegui_pipeline


def crea_scheduler() -> BackgroundScheduler:
    '''Crea uno scheduler configurato per eseguire la pipeline ogni INTERVALLO_MINUTI minuti.'''
    scheduler = BackgroundScheduler()
    scheduler.add_job(esegui_pipeline, 'interval', minutes=config.INTERVALLO_MINUTI)
    return scheduler