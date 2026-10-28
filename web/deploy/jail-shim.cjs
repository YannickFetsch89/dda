// Jailkit blendet /proc aus: Speicher- und CPU-Abfragen von Node schlagen dann fehl.
// Wird per NODE_OPTIONS=--require geladen, damit Next.js bauen und laufen kann.
const os = require("os");
const v8 = require("v8");
const original = process.memoryUsage;
function memoryUsage() {
  try {
    return original.call(process);
  } catch {
    const h = v8.getHeapStatistics();
    return { rss: h.total_heap_size, heapTotal: h.total_heap_size, heapUsed: h.used_heap_size, external: h.external_memory, arrayBuffers: 0 };
  }
}
memoryUsage.rss = () => memoryUsage().rss;
process.memoryUsage = memoryUsage;
const cpus = os.cpus;
os.cpus = () => {
  const c = cpus.call(os);
  return c.length ? c : Array.from({ length: 4 }, () => ({ model: "jail", speed: 0, times: { user: 0, nice: 0, sys: 0, idle: 0, irq: 0 } }));
};
if (os.availableParallelism) {
  const ap = os.availableParallelism;
  os.availableParallelism = () => ap.call(os) || 4;
}
