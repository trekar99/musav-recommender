"""Reusable page bodies (wired by the integrated hub or standalone app entrypoints)."""

from collection_playlists.screens.descriptors import render_descriptor_screen
from collection_playlists.screens.overview import render_overview
from collection_playlists.screens.similarity import render_similarity_screen
from collection_playlists.screens.text_search import render_text_search_screen

__all__ = [
    "render_descriptor_screen",
    "render_overview",
    "render_similarity_screen",
    "render_text_search_screen",
]
