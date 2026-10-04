# Product

<!-- impeccable:product-schema 1 -->

## Platform

desktop

## Users

People who want quick access to music while working in other desktop apps.

## Product Purpose

Pulse Music searches music across supported sources and lets users play and manage tracks without leaving their desktop workflow. Success means playback controls remain immediately accessible while search and library tasks stay one action away.

## Positioning

A compact desktop player pairing cross-source music discovery with direct playback controls and a persistent personal library.

## Operating Context

The user keeps a small player beside work applications, searches on demand, and opens the library when managing playlists or recent tracks.

## Capabilities and Constraints

- Windows desktop application built with Python and PySide6, launched as `spotifynano` through the existing npm package.
- Search results aggregate supported music sources; playback availability depends on each source.
- Existing features to preserve: playback, seeking, skip/stop, playlists, shuffle, and recent-play history.
- The compact player target is 380×260 px with an expanded view for search and library.
- Minimize idle CPU, memory, and visual activity; avoid continuous decorative animation and unnecessary background work.

## Brand Commitments

The user requested a pixel-art visual language for this redesign. Keep the existing Pulse Music name and `spotifynano` command.

## Evidence on Hand

- Existing implementation: `music_chat.py`.
- Existing app description and documented behaviors: `README.md`.
- npm command metadata: `npm-package/package.json`.
