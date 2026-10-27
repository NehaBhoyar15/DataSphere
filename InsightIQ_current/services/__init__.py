"""UI-facing service adapters for the AI Data Analytics Assistant.

These modules were missing from the exported project (the ``services``
folder shipped empty), which made every page fail on import. They provide
the local, dependency-light implementations the UI already expects, plus
clear seams where Person 1 (model backend) and Person 2 (database) can
plug in real implementations later.
"""
