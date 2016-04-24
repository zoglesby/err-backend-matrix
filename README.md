# err-backend-matrix

This is a [Matrix](matrix.io) backend for [ErrBot](errbot.io). It allows you (or rather will allow
you, once it's finished) to use ErrBot from within a Matrix chat room.

**NOTE:** This backend is currently not finished, so don't expect it to work.

## Installation

Clone this repository to a directory of your choice, then change the following variables in your
ErrBot `config.py`:

```
BACKEND = 'Matrix'
BOT_EXTRA_BACKEND_DIR = '<path to err-backend-matrix>'
```
