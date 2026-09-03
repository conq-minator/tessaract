def count_error_occurrences(log_filename):
    error_count = 0
    with open(log_filename, "r", encoding="utf-8") as log_file:
        for line in log_file:
            if "ERROR" in line:
                error_count += 1
    return error_count

if __name__ == "__main__":
    filename = "server_runtime.log"
    total_errors = count_error_occurrences(filename)
    print(f"Total system errors found: {total_errors}")
