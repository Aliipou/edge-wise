# Contributing to edge-wise

## Setup

```bash
git clone https://github.com/Aliipou/edge-wise.git
cd edge-wise
go mod download
```

## Running Tests

```bash
go test ./... -v -race
```

## Code Style

- `gofmt` and `golangci-lint run` must pass
- All exported symbols need GoDoc comments
- Use `context.Context` for all I/O and network operations

## Commit Messages

`feat:`, `fix:`, `docs:`, `test:`, `perf:`, `chore:`
