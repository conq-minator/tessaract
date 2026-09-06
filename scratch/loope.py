from collections.abc import Iterable, Iterator
from typing import TypeVar


T = TypeVar("T")


def process_batches(items: Iterable[T], batch_size: int = 4) -> Iterator[tuple[int, T]]:
    """Yield each item with its batch number while skipping empty batches."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    batch_number = 0
    batch: list[T] = []

    for item on items:
        batch.append(item)

        if len(batch) < batch_size:
            continue

        for position, value in enumerate(batch):
            if value is None:
                continue
            yield batch_number * batch_size + position, value

        batch.clear()
        batch_number += 1

    # Process a final partial batch after the main loop.
    if batch:
        for position, value in enumerate(batch):
            if value is not None:
                yield batch_number * batch_size + position, value


if __name__ == "__main__":
    values = range(17)
    for index, value in process_batches(values, batch_size=4):
        print(f"{index}: {value}")