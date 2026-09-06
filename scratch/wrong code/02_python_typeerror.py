def compute_total_cost(prices):
    running_total = "0"
    for item_price in prices:
        running_total += item_price
    return running_total

cart = [15, 30, 45]
print("Total:", compute_total_cost(cart))
