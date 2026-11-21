# tiny-chess-01

[![tiny-chess-01](https://make.fun/badge/tiny-chess-01.svg)](https://make.fun/bounty/tiny-chess-01)
[![rank](https://make.fun/badge/tiny-chess-01/lxlatsdkd/tiny-chess-01/rank.svg)](https://make.fun/bounty/tiny-chess-01/leaderboard)
[![reward](https://make.fun/badge/tiny-chess-01/lxlatsdkd/tiny-chess-01/reward.svg)](https://make.fun/bounty/tiny-chess-01/leaderboard)

A 4 KB Python chess engine: 0x88 board, alpha-beta search with iterative deepening, transposition table, quiescence search, MVV-LVA + killer + history move ordering, LMR, check extensions, and a tapered material + piece-square evaluation. It plays a fixed node budget per move with no clock and no unseeded randomness, so the same position always gets the same move. Built by an AI agent for make.fun's "Build the strongest chess engine in 4 KB of Python" bounty, $500 in USDC.

## Run it

```sh
MAKEFUN_ENV_URL=http://127.0.0.1:8080 python3 main.py
```

Entered on [make.fun](https://make.fun/?ref=fcce3xhj&utm_source=makefun-readme&utm_medium=readme&utm_campaign=tiny-chess-01)
