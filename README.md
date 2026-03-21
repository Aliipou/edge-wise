<div align="center">

[![Go](https://img.shields.io/badge/Go-1.21+-00ADD8?style=flat&amp;logo=go)](https://golang.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

# EdgeWise

**Edge computing platform for distributed IoT workloads with offline-first sync and real-time analytics.**

</div>

## The Challenge

IoT deployments span environments with unreliable connectivity. A factory floor, a remote field station, a ship at sea. Cloud-first architectures fail in these environments because they assume the network is always available.

EdgeWise puts compute at the edge. Devices continue operating when disconnected, sync intelligently when connectivity returns, and analytics run locally without round-tripping to the cloud.

## Architecture

```
IoT Devices
    |
    v
[Edge Node]         Runs on Raspberry Pi, industrial PC, or VM
    |                Collects, processes, and stores data locally
    |                Runs ML inference at the edge
    |
  (sync when connected)
    |
    v
[Cloud Layer]       Aggregates data from all edge nodes
                    Long-term storage, fleet management, global dashboards
```

## Key Features

**Offline-First Operation**
Edge nodes operate fully independently. Data is stored locally using an append-only log. No data loss during network partitions.

**Intelligent Sync**
When connectivity resumes, nodes sync with the cloud using a CRDT-based merge strategy. Conflict resolution is deterministic and requires no manual intervention.

**Local ML Inference**
Deploy TensorFlow Lite or ONNX models to edge nodes. Run inference locally for latency-critical decisions. Models update via the sync layer.

**Real-Time Analytics**
Time-series data is queryable at the edge with sub-millisecond latency. No cloud round-trip needed for local dashboards or control loops.

## Quick Start

```bash
git clone https://github.com/Aliipou/edge-wise.git
cd edge-wise
go build ./cmd/edge-node/
./edge-node --config config/edge.yaml
```

## License

MIT
