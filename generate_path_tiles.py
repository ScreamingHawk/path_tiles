import random


def generate_matchings(points):
    """Recursively yield all perfect matchings on the list of points."""
    if not points:
        yield []
        return
    first = points[0]
    for i in range(1, len(points)):
        second = points[i]
        pair = (first, second)
        rest = points[1:i] + points[i + 1 :]
        for matching in generate_matchings(rest):
            yield [pair] + matching


def main():
    endpoints = list(range(8))
    all_matchings = list(generate_matchings(endpoints))

    print(f"Total perfect matchings on 8 endpoints: {len(all_matchings)}\n")

    sample = random.sample(all_matchings, 36)
    print("Sample of 36 random, unique swirl patterns (each is 4 connected pairs):\n")
    for idx, matching in enumerate(sample, start=1):
        print(f"{idx:2d}: {matching}")


if __name__ == "__main__":
    main()
