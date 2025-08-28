# -*- coding: utf-8 -*-
"""
---------------------------------------
Event System (Design Pattern: Observer)
---------------------------------------

Este módulo implementa o padrão de projeto Observer (também conhecido como Publisher-Subscriber).
Ele permite que objetos (Observers) se inscrevam para receber notificações de outro objeto (Publisher)
quando um evento específico ocorre.

Classes:
- EventPublisher: A classe da qual os "notificadores" devem herdar. Gerencia uma lista de
  observadores e os notifica sobre novos eventos.

- EventObserver: Uma classe base para os "ouvintes". Qualquer classe que queira receber
  notificações deve herdar desta e implementar o método `update`.
"""

class EventPublisher:
    """A classe Subject/Publisher (Notificador)."""
    def __init__(self):
        # Dicionário para armazenar observadores para eventos específicos
        self._observers = {}

    def subscribe(self, event: str, observer):
        """Inscreve um observador para um evento específico."""
        if event not in self._observers:
            self._observers[event] = []
        if observer not in self._observers[event]:
            self._observers[event].append(observer)

    def unsubscribe(self, event: str, observer):
        """Remove a inscrição de um observador de um evento."""
        if event in self._observers:
            try:
                self._observers[event].remove(observer)
            except ValueError:
                pass # O observador não estava na lista

    def notify(self, event: str, data=None):
        """Notifica todos os observadores inscritos em um evento."""
        if event in self._observers:
            for observer in self._observers[event]:
                observer.update(event, data)

class EventObserver:
    """
    A classe base do Observer (Ouvinte).
    Classes concretas devem herdar desta e implementar o método `update`.
    """
    def update(self, event: str, data=None):
        """
        Recebe a atualização do publisher.

        Args:
            event (str): O nome do evento que ocorreu (ex: "params_changed").
            data (any, optional): Os dados associados ao evento.
        """
        raise NotImplementedError("As subclasses devem implementar este método!")
