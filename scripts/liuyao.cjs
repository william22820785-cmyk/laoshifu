#!/usr/bin/env node
'use strict';

void import('@aceworld/liuyao-algorithm/dist/cli.js').catch(error => {
  process.stderr.write(`六爻排盘失败：${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
});
