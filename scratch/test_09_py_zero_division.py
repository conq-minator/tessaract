def calculate_average_rating(ratings, min_threshold=4.0):
    filtered = [r for r in ratings if r >= min_threshold]
    total = sum(filtered)
    return total / len(filtered)

if __name__ == "__main__":
    user_ratings = [3.5, 2.8, 1.0, 3.9]
    avg = calculate_average_rating(user_ratings, min_threshold=4.5)
    print(f"Average high-tier rating: {avg}")
