// -*- coding: utf-8 -*-
// Calcula os pontinhos (meio-tom) do retrato e dos títulos com a mesma técnica
// do caliberda.com.br. Roda num Chrome headless, porque precisa da fonte Archivo
// (carregada do Google Fonts pela própria página) e de canvas para ler a foto.
//
//   node scripts/gera_pontos.js [foto.jpg]
//
// Saída: scripts/pontos.json, lido por gera_pecas.py. Só precisa rodar de novo
// se a foto ou os títulos mudarem. Requisitos: Google Chrome e o pacote "ws".
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

let WebSocket;
try { WebSocket = require('ws'); } catch (e) { WebSocket = require('C:/Dev/caliberda-home/node_modules/ws'); }

const FOTO = process.argv[2] || 'C:/Dev/caliberda-home/julio.jpg';
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const SAIDA = path.join(__dirname, 'pontos.json');

// ── código que roda dentro da página ────────────────────────────────
const PAGINA = `<!doctype html><html><head>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&display=swap">
</head><body><script>
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const r1 = (v) => Math.round(v * 10) / 10;

// Retrato: mesma receita do hero do site (máscara do fundo verde-azulado,
// maior região conectada, nitidez e contraste esticado).
function retrato(img, W, H, COLS) {
  const CROP = { x: 150, y: 100, w: 780 };
  const TRI = [[183, 540], [893, 540], [540, 1045]];
  const sp = W / COLS, cols = COLS, rows = Math.floor(H / sp), N = cols * rows;
  const sh = CROP.w * H / W;
  const off = document.createElement('canvas'); off.width = cols; off.height = rows;
  const o = off.getContext('2d', { willReadFrequently: true });
  o.imageSmoothingQuality = 'high';
  o.drawImage(img, CROP.x, CROP.y, CROP.w, sh, 0, 0, cols, rows);
  const data = o.getImageData(0, 0, cols, rows).data;
  const inc = new Uint8Array(N), L = new Float32Array(N);
  for (let k = 0; k < N; k++) {
    const R = data[k * 4], G = data[k * 4 + 1], B = data[k * 4 + 2];
    const lum = (0.299 * R + 0.587 * G + 0.114 * B) / 255;
    L[k] = lum;
    inc[k] = ((G + B) / 2 - R < 12 && !(G - R > 5 && lum < 0.3)) ? 1 : 0;
  }
  const lab = new Int32Array(N).fill(-1), st = [];
  let best = -1, bestSize = 0, id = 0;
  for (let k = 0; k < N; k++) {
    if (!inc[k] || lab[k] >= 0) continue;
    let size = 0; lab[k] = id; st.push(k);
    while (st.length) {
      const c = st.pop(); size++;
      const cx = c % cols, cy = (c / cols) | 0;
      [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dx, dy]) => {
        const nx = cx + dx, ny = cy + dy;
        if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) return;
        const n = ny * cols + nx;
        if (inc[n] && lab[n] < 0) { lab[n] = id; st.push(n); }
      });
    }
    if (size > bestSize) { bestSize = size; best = id; }
    id++;
  }
  const S2 = new Float32Array(N);
  for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) {
    let sum = 0, cnt = 0;
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
      const nx = x + dx, ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) continue;
      sum += L[ny * cols + nx]; cnt++;
    }
    const k = y * cols + x;
    S2[k] = clamp(L[k] + 0.9 * (L[k] - sum / cnt));
  }
  const vals = [];
  for (let k = 0; k < N; k++) if (lab[k] === best) vals.push(S2[k]);
  vals.sort((a, b) => a - b);
  const lo = vals[Math.floor(vals.length * 0.02)], hi = vals[Math.floor(vals.length * 0.98)];
  const pts = [];
  for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) {
    const k = y * cols + x;
    if (lab[k] !== best) continue;
    pts.push([r1(sp / 2 + x * sp), r1(sp / 2 + y * sp), Math.round(clamp((S2[k] - lo) / (hi - lo)) * 100) / 100]);
  }
  const tri = TRI.map(([x, y]) => [r1((x - CROP.x) / CROP.w * W), r1((y - CROP.y) / sh * H)]);
  return { w: W, h: H, sp: r1(sp), pts, tri };
}

// Texto em pontos: desenha grande, mede o contorno real pelos pixels e
// reamostra numa grade, guardando a cobertura (0..1) de cada célula.
function texto(linhas, cel, alturaLinha, opts) {
  const F = 400, pad = 80;
  const big = document.createElement('canvas');
  const larg = 4200, alt = pad * 2 + F * linhas.length;
  big.width = larg; big.height = alt;
  const g = big.getContext('2d', { willReadFrequently: true });
  g.fillStyle = '#fff'; g.textBaseline = 'alphabetic';
  g.font = opts.peso + ' ' + F + 'px "Archivo", sans-serif';
  if ('fontStretch' in g) g.fontStretch = opts.largura || 'normal';
  const larguras = [];
  linhas.forEach((ln, i) => {
    const x = pad + (ln.recuo || 0) * F;
    g.fillText(ln.t, x, pad + F * 0.8 + i * F * opts.entrelinha);
    larguras.push({ x0: x, x1: x + g.measureText(ln.t).width });
  });
  const d = g.getImageData(0, 0, larg, alt).data;
  let x0 = larg, x1 = 0, y0 = alt, y1 = 0;
  for (let y = 0; y < alt; y += 2) for (let x = 0; x < larg; x += 2) {
    if (d[(y * larg + x) * 4 + 3] > 40) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  }
  // escala: a altura total do bloco vira "alturaLinha" unidades por linha
  const k = (alturaLinha * linhas.length) / (y1 - y0);
  const W = (x1 - x0) * k, H = (y1 - y0) * k;
  const cols = Math.ceil(W / cel), rows = Math.ceil(H / cel);
  const off = document.createElement('canvas'); off.width = cols; off.height = rows;
  const o = off.getContext('2d', { willReadFrequently: true });
  o.imageSmoothingQuality = 'high';
  o.drawImage(big, x0, y0, x1 - x0, y1 - y0, 0, 0, (x1 - x0) * k / cel, (y1 - y0) * k / cel);
  const od = o.getImageData(0, 0, cols, rows).data;
  const pts = [];
  for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) {
    const a = od[(y * cols + x) * 4 + 3] / 255;
    if (a < 0.1) continue;
    pts.push([r1(cel / 2 + x * cel), r1(cel / 2 + y * cel), Math.round(a * 100) / 100]);
  }
  // onde termina cada linha (para o quadradinho azul depois do nome)
  const fim = larguras.map((l) => r1((l.x1 - x0) * k));
  return { w: r1(W), h: r1(H), cel, pts, fim };
}

window.gera = async (foto) => {
  await document.fonts.load('800 100px "Archivo"');
  await document.fonts.ready;
  const img = new Image(); img.src = foto; await img.decode();
  return {
    retrato: retrato(img, 360, 450, 66),
    nome: texto([{ t: 'JÚLIO' }, { t: 'CALIBERDA', recuo: 0.32 }], 4.3, 92, { peso: 800, largura: 'condensed', entrelinha: 0.84 }),
    portfolio: texto([{ t: 'PORTFÓLIO' }], 3.2, 58, { peso: 800, largura: 'condensed', entrelinha: 1 }),
    portfolioEn: texto([{ t: 'PORTFOLIO' }], 3.2, 58, { peso: 800, largura: 'condensed', entrelinha: 1 }),
  };
};
</script></body></html>`;

// ── orquestração via Chrome DevTools Protocol ───────────────────────
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const getJSON = (u) => new Promise((res, rej) => http.get(u, (r) => { let d = ''; r.on('data', (c) => d += c); r.on('end', () => { try { res(JSON.parse(d)); } catch (e) { rej(e); } }); }).on('error', rej));

(async () => {
  const port = 9500 + Math.floor(Math.random() * 400);
  const udd = path.join(require('os').tmpdir(), 'gera-pontos-' + port);
  const chrome = spawn(CHROME, ['--headless=new', '--remote-debugging-port=' + port, '--user-data-dir=' + udd, 'about:blank'], { stdio: 'ignore' });
  try {
    let list;
    for (let i = 0; i < 60; i++) { try { list = await getJSON('http://127.0.0.1:' + port + '/json'); break; } catch (e) { await sleep(200); } }
    const ws = new WebSocket(list.find((t) => t.type === 'page').webSocketDebuggerUrl);
    await new Promise((r) => ws.on('open', r));
    let id = 0; const pend = {};
    ws.on('message', (m) => { const d = JSON.parse(m); if (d.id && pend[d.id]) { pend[d.id](d); delete pend[d.id]; } });
    const send = (method, params = {}) => new Promise((r) => { const i = ++id; pend[i] = r; ws.send(JSON.stringify({ id: i, method, params })); });

    await send('Page.enable');
    const frame = (await send('Page.getFrameTree')).result.frameTree.frame.id;
    await send('Page.setDocumentContent', { frameId: frame, html: PAGINA });
    await sleep(1500);
    const foto = 'data:image/jpeg;base64,' + fs.readFileSync(FOTO).toString('base64');
    const r = await send('Runtime.evaluate', { expression: 'gera(' + JSON.stringify(foto) + ')', awaitPromise: true, returnByValue: true });
    if (r.result.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails));
    const dados = r.result.result.value;
    fs.writeFileSync(SAIDA, JSON.stringify(dados));
    console.log('pontos: retrato %d · nome %d · portfólio %d → %s',
      dados.retrato.pts.length, dados.nome.pts.length, dados.portfolio.pts.length, SAIDA);
    ws.close();
  } finally {
    chrome.kill();
    setTimeout(() => { try { fs.rmSync(udd, { recursive: true, force: true }); } catch (e) { } }, 500);
  }
})().catch((e) => { console.error(e); process.exit(1); });
