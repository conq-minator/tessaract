/**
 * Session Manager: Tracks active session ID and monotonic sequence numbers.
 */

import { v4 as uuidv4 } from 'uuid';

export class SessionManager {
    private static instance: SessionManager;
    private sessionId: string;
    private sequenceNumber: number = 0;

    private constructor() {
        this.sessionId = uuidv4();
    }

    public static getInstance(): SessionManager {
        if (!this.instance) {
            this.instance = new SessionManager();
        }
        return this.instance;
    }

    public getSessionId(): string {
        return this.sessionId;
    }

    public nextSequence(): number {
        return ++this.sequenceNumber;
    }

    public resetSession(): string {
        this.sessionId = uuidv4();
        this.sequenceNumber = 0;
        return this.sessionId;
    }
}
