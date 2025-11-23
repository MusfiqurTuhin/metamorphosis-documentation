# ui/__init__.py

"""UI package for Metamorphosis Studio.
Provides a single entry point `render_tabs` that builds the Streamlit tab interface.
The heavy business logic is delegated to the service layer (`services.helpers`).
"""

from .tabs import render_tabs  # noqa: F401
