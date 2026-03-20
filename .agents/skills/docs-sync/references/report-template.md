# Docs 同步审计报告

> 日期：YYYY-MM-DD

## 概要

| Phase | P0 | P1 | P2 |
|-------|----|----|-----|
| A（链接完整性） | N | N | — |
| B（guide↔reference） | — | N | N |
| C（examples） | — | N | — |
| D（Code↔Docs） | N | N | N |
| **合计** | **N** | **N** | **N** |

## P0 — 必须修复

| # | Phase | 类型 | 文件 | 行号 | 详情 |
|---|-------|------|------|------|------|
| 1 | A | BROKEN_LINK | `guide/3/xxx.md` | L42 | link `<path>` → not found |

## P1 — 应当修复

| # | Phase | 类型 | 文件 | 行号 | 详情 |
|---|-------|------|------|------|------|
| 1 | B | GUIDE_REF_MISMATCH | `guide/xxx` vs `reference/xxx` | L15/L30 | API 签名不一致 |

## P2 — 仅报告

| # | Phase | 类型 | 文件 | 行号 | 详情 |
|---|-------|------|------|------|------|
| 1 | D | API_UNDOCUMENTED | `ncatbot/xxx/yyy.py` | — | 新增 API 无文档 |

## 修复记录

| # | 问题 | 修复操作 | 状态 |
|---|------|---------|------|
| 1 | ... | ... | ✅ / ⏳ |
