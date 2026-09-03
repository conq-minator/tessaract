/**
 * Event-Driven Pub/Sub Architecture with Wildcard Support.
 * Demonstrates closures, callback registries, once-listeners, and safe listener dispatch.
 */

class EventEmitter {
    constructor(maxListeners = 10) {
        this._events = new Map();
        this._maxListeners = maxListeners;
    }

    on(eventName, listener) {
        if (typeof listener !== 'function') {
            throw new TypeError('Listener must be a callable function');
        }

        if (!this._events.has(eventName)) {
            this._events.set(eventName, []);
        }

        const listeners = this._events.get(eventName);
        if (listeners.length >= this._maxListeners) {
            console.warn(`[Warning] MaxListeners (${this._maxListeners}) exceeded on event '${eventName}'`);
        }

        listeners.push(listener);
        return () => this.off(eventName, listener); // Unsubscribe helper
    }

    once(eventName, listener) {
        const wrapper = (...args) => {
            this.off(eventName, wrapper);
            listener.apply(this, args);
        };
        wrapper._original = listener;
        return this.on(eventName, wrapper);
    }

    off(eventName, listener) {
        if (!this._events.has(eventName)) return this;
        const listeners = this._events.get(eventName);
        const index = listeners.findIndex(fn => fn === listener || fn._original === listener);
        if (index !== -1) {
            listeners.splice(index, 1);
        }
        if (listeners.length === 0) {
            this._events.delete(eventName);
        }
        return this;
    }

    emit(eventName, ...args) {
        let delivered = 0;
        // Direct event listeners
        if (this._events.has(eventName)) {
            const listeners = [...this._events.get(eventName)]; // copy to prevent mutation during emit
            for (const fn of listeners) {
                try {
                    fn.apply(this, args);
                    delivered++;
                } catch (err) {
                    console.error(`[Error] Unhandled listener exception in '${eventName}':`, err);
                }
            }
        }

        // Wildcard '*' listeners
        if (eventName !== '*' && this._events.has('*')) {
            const wildcardListeners = [...this._events.get('*')];
            for (const fn of wildcardListeners) {
                try {
                    fn.call(this, eventName, ...args);
                    delivered++;
                } catch (err) {
                    console.error(`[Error] Wildcard exception on '${eventName}':`, err);
                }
            }
        }

        return delivered > 0;
    }

    listenerCount(eventName) {
        return this._events.has(eventName) ? this._events.get(eventName).length : 0;
    }
}

// Verification Routine
function runDemo() {
    console.log('[EventEmitter Demo] Initializing Event-Driven PubSub Channel...');
    const emitter = new EventEmitter();
    const eventLog = [];

    // Subscribe standard handler
    const unsubTelemetry = emitter.on('telemetry', (data) => {
        eventLog.push(`Telemetry: ${data.metric}=${data.value}`);
    });

    // Subscribe once handler
    emitter.once('login', (user) => {
        eventLog.push(`User Authenticated: ${user.name}`);
    });

    // Subscribe wildcard handler
    emitter.on('*', (eventName, payload) => {
        console.log(` -> Audit log [Wildcard] intercepted: [${eventName}]`);
    });

    emitter.emit('login', { name: 'Alice' });
    emitter.emit('login', { name: 'Bob' }); // Should NOT trigger the 'once' listener
    emitter.emit('telemetry', { metric: 'cpu_usage', value: '42%' });

    console.log('Event Log Records:');
    eventLog.forEach(l => console.log('  ', l));

    if (eventLog.length === 2 && eventLog[0].includes('Alice') && !eventLog.some(l => l.includes('Bob'))) {
        console.log('[EventEmitter Demo] Status: SUCCESS - Event dispatching and once-lifecycle verified.');
    }
}

runDemo();
