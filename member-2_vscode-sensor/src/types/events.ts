/**
 * Tesseract Event Definitions conforming to Member 4 Core Engine schemas.
 */

export type EventType =
    | 'file_opened'
    | 'file_saved'
    | 'file_closed'
    | 'file_edited'
    | 'error_detected'
    | 'error_resolved'
    | 'terminal_command'
    | 'terminal_output'
    | 'debug_started'
    | 'debug_ended'
    | 'debug_breakpoint_hit'
    | 'workspace_changed';

export interface EventMetadata {
    session_id: string;
    sequence_number: number;
    confidence: number;
    privacy_level: 'local_only' | 'anonymized';
    version: string;
}

export interface BasePayload {
    [key: string]: unknown;
}

export interface FileOpenedPayload extends BasePayload {
    file_path: string;
    language: string;
    workspace?: string;
}

export interface FileSavedPayload extends BasePayload {
    file_path: string;
    language: string;
    change_size: number;
    line_count: number;
}

export interface FileClosedPayload extends BasePayload {
    file_path: string;
    language: string;
    duration_ms: number;
}

export interface FileEditedPayload extends BasePayload {
    file_path: string;
    language: string;
    line_count: number;
    change_character_count: number;
}

export interface ErrorDetectedPayload extends BasePayload {
    file_path: string;
    language: string;
    error_message: string;
    error_line: number;
    severity: 'error' | 'warning' | 'info';
    source?: string;
}

export interface ErrorResolvedPayload extends BasePayload {
    file_path: string;
    language: string;
    error_message: string;
    error_line: number;
}

export interface TerminalCommandPayload extends BasePayload {
    command: string;
    exit_code?: number;
    duration_ms?: number;
}

export interface DebugPayload extends BasePayload {
    session_name: string;
    debug_type: string;
    file_path?: string;
    line?: number;
}

export interface TesseractEvent<T extends BasePayload = BasePayload> {
    event_id: string;
    source: 'vscode';
    event_type: EventType;
    timestamp: string;
    payload: T;
    metadata: EventMetadata;
}
