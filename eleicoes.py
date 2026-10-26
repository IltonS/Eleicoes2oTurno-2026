#!/usr/bin/env python3
"""Acompanha ao vivo o resultado da eleição presidencial no site do TSE.

O site (resultados.tse.jus.br) é uma SPA que lê um arquivo JWS assinado; o
payload desse JWS é um JSON com a totalização. Este script baixa esse arquivo
periodicamente e mostra os votos de cada candidato e a diferença entre eles.

Uso:
    python3 eleicoes.py              # atualiza a cada 1 segundo
    python3 eleicoes.py -i 5         # atualiza a cada 5 segundos
    python3 eleicoes.py --once       # imprime uma vez e sai
"""

import argparse
import base64
import json
import sys
import time
import urllib.request
from datetime import datetime

ELEICAO = "6258"   # 2º turno 2026
CARGO = "0001"     # Presidente
UF = "br"
URL = (
    f"https://resultados.tse.jus.br/oficial/ele2026/{ELEICAO}/dados/{UF}/"
    f"{UF}-c{CARGO}-e{int(ELEICAO):06d}-u.jws"
)
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)

BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"
RESET = "\033[0m"


def fetch(timeout=10):
    url = f"{URL}?nocache={int(time.time() * 1000)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("ascii").strip()


def decode_jws(token):
    """Decodifica o payload de um JWS compacto (a assinatura não é verificada)."""
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def parse(data):
    candidatos = []
    for cargo in data.get("carg", []):
        for agr in cargo.get("agr", []):
            for par in agr.get("par", []):
                for cand in par.get("cand", []):
                    candidatos.append({
                        "nome": cand.get("nmu") or cand.get("nm"),
                        "numero": cand.get("n"),
                        "partido": par.get("sg", ""),
                        "votos": int(cand.get("vap") or 0),
                        "pct": float((cand.get("pvapn") or cand.get("pvap") or "0").replace(",", ".")),
                        "eleito": cand.get("e") == "s",
                    })
    candidatos.sort(key=lambda c: c["votos"], reverse=True)

    s, v, e = data.get("s", {}), data.get("v", {}), data.get("e", {})
    return {
        "atualizacao": f"{data.get('dg', '?')} {data.get('hg', '')}".strip(),
        "secoes_pct": s.get("pst", "?"),
        "secoes": int(s.get("st") or 0),
        "secoes_total": int(s.get("ts") or 0),
        "validos": int(v.get("vv") or 0),
        "brancos": int(v.get("vb") or 0),
        "nulos": int(v.get("tvn") or 0),
        "comparecimento": int(e.get("c") or 0),
        "abstencao": int(e.get("a") or 0),
        "eleitores": int(e.get("te") or 0),
        "candidatos": candidatos,
    }


def fmt(n):
    """Formata inteiro com separador de milhar brasileiro."""
    return f"{n:,}".replace(",", ".")


def fmt_pct(x, casas=2):
    return f"{x:.{casas}f}".replace(".", ",")


def render(res, anterior=None, erro=None):
    out = ["\033[H\033[2J"]
    out.append(f"{BOLD}Eleição Presidencial 2026 – 2º turno (TSE){RESET}")
    out.append(
        f"Atualização TSE: {res['atualizacao']}   "
        f"Seções apuradas: {BOLD}{res['secoes_pct']}%{RESET} "
        f"({fmt(res['secoes'])} de {fmt(res['secoes_total'])})"
    )
    out.append(f"{DIM}Hora local: {datetime.now():%H:%M:%S}{RESET}")
    out.append("")

    cands = res["candidatos"]
    largura = max((len(c["nome"]) for c in cands), default=10) + 2
    out.append(f"{'Candidato':<{largura}}{'Nº':>4}  {'Votos':>14}  {'%':>8}")
    out.append("-" * (largura + 32))
    for i, c in enumerate(cands):
        cor = GREEN if i == 0 else ""
        marca = f"  {GREEN}{BOLD}ELEITO{RESET}" if c["eleito"] else ""
        out.append(
            f"{cor}{c['nome']:<{largura}}{c['numero']:>4}  {fmt(c['votos']):>14}  "
            f"{fmt_pct(c['pct']):>7}%{RESET}{marca}"
        )
    out.append("")

    if len(cands) >= 2:
        lider, segundo = cands[0], cands[1]
        diff = lider["votos"] - segundo["votos"]
        diff_pp = lider["pct"] - segundo["pct"]
        out.append(
            f"{BOLD}Diferença: {YELLOW}{fmt(diff)} votos{RESET}{BOLD} "
            f"({fmt_pct(diff_pp, 4)} p.p.) a favor de {lider['nome']}{RESET}"
        )

        if anterior:
            votos_ant = {c["numero"]: c["votos"] for c in anterior["candidatos"]}
            deltas = [
                f"{c['nome']} +{fmt(c['votos'] - votos_ant.get(c['numero'], 0))}"
                for c in cands
            ]
            if any(c["votos"] != votos_ant.get(c["numero"]) for c in cands):
                out.append(f"Última atualização: {', '.join(deltas)}")

    out.append("")
    out.append(
        f"Válidos: {fmt(res['validos'])}   Brancos: {fmt(res['brancos'])}   "
        f"Nulos: {fmt(res['nulos'])}"
    )
    out.append(
        f"Comparecimento: {fmt(res['comparecimento'])}   "
        f"Abstenção: {fmt(res['abstencao'])}   Eleitorado: {fmt(res['eleitores'])}"
    )
    if erro:
        out.append("")
        out.append(f"{RED}Erro na última consulta: {erro}{RESET}")
    out.append(f"\n{DIM}Ctrl+C para sair{RESET}")
    print("\n".join(out), flush=True)


def main():
    ap = argparse.ArgumentParser(description="Resultados ao vivo do TSE no terminal.")
    ap.add_argument("-i", "--interval", type=float, default=1.0,
                    help="intervalo entre atualizações em segundos (padrão: 1)")
    ap.add_argument("--once", action="store_true", help="consulta uma vez e sai")
    args = ap.parse_args()

    atual = None      # último resultado obtido
    anterior = None   # resultado antes da última mudança nos dados do TSE
    try:
        while True:
            erro = None
            try:
                novo = parse(decode_jws(fetch()))
                if atual and novo["atualizacao"] != atual["atualizacao"]:
                    anterior = atual
                atual = novo
            except Exception as exc:  # rede/parse: mantém o último resultado
                erro = exc
                if atual is None and args.once:
                    sys.exit(f"Erro: {exc}")

            if atual:
                render(atual, anterior, erro)
            else:
                print(f"Aguardando dados do TSE... ({erro})", flush=True)

            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
