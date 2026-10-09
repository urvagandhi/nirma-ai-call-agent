---
name: react-best-practices
description: React 19 and frontend performance optimization guidelines from Vercel Engineering for high-throughput interfaces and WebSocket streams.
---

# React Best Practices

High-performance architecture for React applications.

## High-Frequency WebSocket Optimization
- **Do not store fast-ticking streams in root component state**: Keep high-rate incoming audio/STT chunks in a `useRef` or isolated leaf component to avoid re-rendering entire data tables and dashboards.
- **Batch state updates**: Group incoming status events into animation frames or micro-batches.
- **Memoize heavy components**: Use `React.memo`, `useMemo`, and `useCallback` on data tables and audio visualizer canvas elements.
- **Direct import paths**: Avoid bloated barrel files.
