function loadDatabaseConfig(rawConfigPayload) {
    const parsed = JSON.parse(rawConfigPayload);
    return {
        host: parsed.host,
        port: parsed.port || 5432,
        database: parsed.database
    };
}

const incomingWebhookPayload = `{
    "host": "localhost",
    "port": 5432,
    "database": "analytics_db",
}`;

const config = loadDatabaseConfig(incomingWebhookPayload);
console.log("Database connected to:", config.host, config.port);
