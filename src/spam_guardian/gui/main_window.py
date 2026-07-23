"""
Finestra principale: mostra le email classificate, permette di correggere
la categoria assegnata dal modello, controlla l'avvio/stop dello scheduler
e vive nella system tray per restare in background.
"""

import sys
from functools import partial

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QComboBox,
    QPushButton, QLabel, QSystemTrayIcon, QMenu, QStyle,
)
from PySide6.QtGui import QAction

from ..core.scheduler import crea_scheduler
from ..db import database, repository
from ..llm.classifier import CATEGORIE


class FinestraPrincipale(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('AI Spam Guardian')
        self.resize(600, 450)

        self.connessione = database.crea_connessione()
        database.crea_schema(self.connessione)
        self.email = repository.leggi_email_classificate(self.connessione)

        self.scheduler = None

        layout = QVBoxLayout(self)
        layout.addLayout(self._crea_controlli_scheduler())

        self.tabella = QTableWidget(len(self.email), 2)
        self.tabella.setHorizontalHeaderLabels(['Oggetto', 'Categoria'])
        layout.addWidget(self.tabella)

        self._popola_tabella()

        layout.addLayout(self._crea_sezione_log())
        self._aggiorna_log()

        self._crea_tray_icon()

    def _crea_controlli_scheduler(self) -> QHBoxLayout:
        '''Riga con etichetta di stato e pulsanti avvia/ferma scheduler.'''
        self.etichetta_stato = QLabel('Scheduler: fermo')

        self.pulsante_avvia = QPushButton('Avvia')
        self.pulsante_avvia.clicked.connect(self._avvia_scheduler)

        self.pulsante_ferma = QPushButton('Ferma')
        self.pulsante_ferma.clicked.connect(self._ferma_scheduler)
        self.pulsante_ferma.setEnabled(False)

        riga = QHBoxLayout()
        riga.addWidget(self.etichetta_stato)
        riga.addWidget(self.pulsante_avvia)
        riga.addWidget(self.pulsante_ferma)
        return riga

    def _avvia_scheduler(self) -> None:
        '''Crea e avvia lo scheduler; aggiorna stato e pulsanti.'''
        self.scheduler = crea_scheduler()
        self.scheduler.start()

        self.etichetta_stato.setText('Scheduler: attivo')
        self.pulsante_avvia.setEnabled(False)
        self.pulsante_ferma.setEnabled(True)

    def _ferma_scheduler(self) -> None:
        '''Ferma lo scheduler in esecuzione; aggiorna stato e pulsanti.'''
        self.scheduler.shutdown()
        self.scheduler = None

        self.etichetta_stato.setText('Scheduler: fermo')
        self.pulsante_avvia.setEnabled(True)
        self.pulsante_ferma.setEnabled(False)

    def _crea_tray_icon(self) -> None:
        '''Crea l'icona nella system tray, con menu "Mostra finestra" / "Esci".'''
        icona = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)

        self.tray_icon = QSystemTrayIcon(icona, self)
        self.tray_icon.setToolTip('AI Spam Guardian')

        menu = QMenu()

        azione_mostra = QAction('Mostra finestra', self)
        azione_mostra.triggered.connect(self._mostra_finestra)
        menu.addAction(azione_mostra)

        azione_esci = QAction('Esci', self)
        azione_esci.triggered.connect(self._esci)
        menu.addAction(azione_esci)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._tray_attivata)
        self.tray_icon.show()

    def _mostra_finestra(self) -> None:
        '''Riporta in primo piano la finestra principale.'''
        self.show()
        self.raise_()
        self.activateWindow()

    def _tray_attivata(self, motivo) -> None:
        '''Doppio clic sull'icona tray: mostra la finestra.'''
        if motivo == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._mostra_finestra()

    def _esci(self) -> None:
        '''Chiude davvero l'app (ferma lo scheduler, se attivo, prima di uscire).'''
        if self.scheduler is not None:
            self.scheduler.shutdown()
        QApplication.quit()

    def closeEvent(self, event) -> None:
        '''Clic sulla X: nasconde la finestra nella tray invece di chiudere l'app.'''
        event.ignore()
        self.hide()

    def _crea_sezione_log(self) -> QVBoxLayout:
        '''Etichetta, pulsante "Aggiorna" e tabella del log delle esecuzioni.'''
        intestazione = QHBoxLayout()
        intestazione.addWidget(QLabel('Log esecuzioni'))
        pulsante_aggiorna = QPushButton('Aggiorna')
        pulsante_aggiorna.clicked.connect(self._aggiorna_log)
        intestazione.addWidget(pulsante_aggiorna)

        self.tabella_log = QTableWidget(0, 4)
        self.tabella_log.setHorizontalHeaderLabels(['Data', 'Lette', 'Nuove', 'Errori'])

        sezione = QVBoxLayout()
        sezione.addLayout(intestazione)
        sezione.addWidget(self.tabella_log)
        return sezione

    def _aggiorna_log(self) -> None:
        '''Rilegge il log delle esecuzioni dal DB e aggiorna la tabella.'''
        log = repository.leggi_log_esecuzioni(self.connessione)
        self.tabella_log.setRowCount(len(log))

        for riga, esecuzione in enumerate(log):
            self.tabella_log.setItem(riga, 0, QTableWidgetItem(esecuzione['data_esecuzione']))
            self.tabella_log.setItem(riga, 1, QTableWidgetItem(str(esecuzione['email_lette'])))
            self.tabella_log.setItem(riga, 2, QTableWidgetItem(str(esecuzione['email_nuove'])))
            self.tabella_log.setItem(riga, 3, QTableWidgetItem(str(esecuzione['errori'])))

    def _popola_tabella(self) -> None:
        '''Riempie la tabella con una riga per email e un menu a tendina per la categoria.'''
        for riga, email in enumerate(self.email):
            self.tabella.setItem(riga, 0, QTableWidgetItem(email['oggetto']))

            combo = QComboBox()
            combo.addItems(CATEGORIE)
            combo.setCurrentText(email['categoria'])
            combo.currentTextChanged.connect(partial(self._categoria_cambiata, email))
            self.tabella.setCellWidget(riga, 1, combo)

    def _categoria_cambiata(self, email: dict, nuova_categoria: str) -> None:
        '''Chiamata quando scegli una categoria diversa dal menu a tendina.'''
        if nuova_categoria == email['categoria']:
            return

        repository.salva_feedback(
            self.connessione,
            email_id=email['id'],
            categoria_originale=email['categoria'],
            categoria_corretta=nuova_categoria,
        )
        print(f'Feedback salvato: {email["oggetto"][:40]!r} -> {nuova_categoria}')


def avvia_finestra() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    finestra = FinestraPrincipale()
    finestra.show()
    sys.exit(app.exec())