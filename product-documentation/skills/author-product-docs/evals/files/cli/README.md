# tidyfs

tidyfs is a command-line tool for organizing files, written in Python with argparse.

## Options

| Flag | Description |
| --- | --- |
| `-h`, `--help` | Show help and exit |
| `-v`, `--verbose` | Print each action |
| `-n`, `--dry-run` | Show actions without applying them |
| `-r`, `--recursive` | Descend into subdirectories |
| `-b`, `--by {ext,date,size}` | Grouping rule |
| `-o`, `--output DIR` | Destination directory |
| `-x`, `--exclude GLOB` | Skip matching files (repeatable) |
| `--follow-symlinks` | Follow symbolic links |
| `--config FILE` | Read options from a file |
| `--log-level LEVEL` | One of debug, info, warning, error |

## Installation

```
pip install tidyfs
```

## License

MIT
