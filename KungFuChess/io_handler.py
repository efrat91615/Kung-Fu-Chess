from __future__ import annotations

from typing import TextIO


class IOHandler:
    def __init__(self, reader: TextIO, writer: TextIO) -> None:
        self._reader = reader
        self._writer = writer

    @property
    def reader(self) -> TextIO:
        return self._reader

    @property
    def writer(self) -> TextIO:
        return self._writer

    def write(self, message: str, end: str = "\n") -> None:
        self._writer.write(f"{message}{end}")
