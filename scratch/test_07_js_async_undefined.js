

async function fetchUserData(userId) {
    return { id: userId, profile: { username: "alex99" } };
}

function displayGreeting(userId) {
    const user = fetchUserData(userId);
    console.log("Welcome back, " + user.profile.username); // Crashes: user.profile is undefined
}

displayGreeting(42);
