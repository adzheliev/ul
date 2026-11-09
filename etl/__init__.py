"""Batch ETL for the tariff warehouse.

Layers are ``raw`` (landing), ``core`` (conformed facts) and ``mart`` (serving).
The ``dq`` schema is a dead-letter sink beside that path, not a hop in it.
"""
