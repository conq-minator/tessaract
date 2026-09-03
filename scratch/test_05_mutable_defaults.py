"""
Test Case 05: Python Mutable Default Argument Bug
Expected Error: Unexpected state leakage / test assertion failure
Testing: Can Tesseract detect shared state across function invocations?
"""

def append_task(task_name, task_list=[]):
    # Bug: mutable default list persists across distinct function calls
    task_list.append(task_name)
    return task_list

if __name__ == "__main__":
    user1_tasks = append_task("Write docs")
    user2_tasks = append_task("Fix bug")
    
    print("User 2 tasks:", user2_tasks)
    # Assertion fails because user2 received user1's task
    assert len(user2_tasks) == 1, f"Expected 1 task, but got {len(user2_tasks)}: {user2_tasks}"
