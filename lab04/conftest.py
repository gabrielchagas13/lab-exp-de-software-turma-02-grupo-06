"""Põe a raiz do lab04 no sys.path para que `tests/` importe `simulacao`
sem precisar instalar o pacote.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
