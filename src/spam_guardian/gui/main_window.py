"""
Finestra principale: mostra le email classificate e permette di correggere
la categoria assegnata dal modello.
"""

import sys
from functools import partial

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QComboBox,
)

from ..db import database, repository
from ..llm.classifier import CATEGORIE


class FinestraPrincipale(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('AI Spam Guardian — Rivedi classificazioni')
        self.resize(600, 400)

        self.connessione = database.crea_connessione()
        database.crea_schema(self.connessione)
        self.email = repository.leggi_email_classificate(self.connessione)

        layout = QVBoxLayout(self)
        self.tabella = QTableWidget(len(self.email), 2)
        self.tabella.setHorizontalHeaderLabels(['Oggetto', 'Categoria'])
        layout.addWidget(self.tabella)

        self._popola_tabella()

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
            return  # non è una vera correzione

        repository.salva_feedback(
            self.connessione,
            email_id=email['id'],
            categoria_originale=email['categoria'],
            categoria_corretta=nuova_categoria,
        )
        print(f'Feedback salvato: {email["oggetto"][:40]!r} -> {nuova_categoria}')


def avvia_finestra() -> None:
    app = QApplication(sys.argv)
    finestra = FinestraPrincipale()
    finestra.show()
    sys.exit(app.exec())