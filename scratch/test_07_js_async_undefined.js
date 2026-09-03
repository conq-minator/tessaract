/**
 * Test Case 07: JavaScript Unhandled Promise & Undefined Traversal
 * Expected Error: TypeError: Cannot read properties of undefined (reading 'username')
 * Testing: Can Tesseract detect missing await or undefined object property access?
 */

async function fetchUserData(userId) {
    return { id: userId, profile: { username: "alex99" } };
}

function displayGreeting(userId) {
    // Bug: forgot 'await', so user is a Promise, not the resolved object
    const user = fetchUserData(userId);
    console.log("Welcome back, " + user.profile.username); // Crashes: user.profile is undefined
}

displayGreeting(42);
