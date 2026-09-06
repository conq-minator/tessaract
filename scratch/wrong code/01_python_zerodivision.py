def calculate_average(scores):
    total = sum(scores)
    return total / len(scores)

test_scores = []
print("Average score:", calculate_average(test_scores))
