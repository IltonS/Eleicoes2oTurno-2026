# Eleições 2º Turno

A simple CLI that follows the 2026 Brazilian presidential election (2nd round) live in the
terminal. It reads the official results from the TSE site
([resultados.tse.jus.br](https://resultados.tse.jus.br/oficial/app/index.html#/eleicao/6258/uf/br/cargo/1/vis/nominal/resultados)),
refreshes every second and shows:

- votes and percentage for each candidate
- the vote difference between the leader and the runner-up
- percentage of polling sections counted and time of the last TSE update
- valid, blank and null votes, turnout and abstention

It uses only the Python standard library (Python 3.8+).

## Getting started

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the app:

```bash
python3 eleicoes.py
```

Press `Ctrl+C` to exit.

### Options

| Option | Description |
| --- | --- |
| `-i`, `--interval SECONDS` | Time between refreshes (default: `1`) |
| `--once` | Fetch the results once and exit |

Example, refreshing every 5 seconds:

```bash
python3 eleicoes.py -i 5
```

To follow another election or office, change `ELEICAO` and `CARGO` at the top of `eleicoes.py`.

## License

[MIT](LICENSE)
