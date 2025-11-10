/* Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
 * Redistribution of original or derived work requires permission of course staff.
 */
import assert from 'node:assert';
import fs from 'node:fs';
import { Card } from './models/Card.js';
import { Player } from './models/Player.js';
import { Deferred } from './utils/Deferred.js';
/**
 * Mutable Board ADT representing a Memory Scramble game board.
 *
 * The board is a grid of cards that multiple players can interact with concurrently.
 * Players can flip cards to find matching pairs, and the board handles concurrent
 * access with proper waiting and synchronization according to the game rules.
 *
 * This ADT is thread-safe and handles concurrent operations correctly.
 *
 * Specification:
 * - Board represents a rows x cols grid of cards
 * - Multiple players can interact with the board concurrently
 * - Players flip cards to find matching pairs
 * - When a player flips a first card, they control it (waiting if another player controls it)
 * - When a player flips a second card, matched cards are removed on the next move
 * - Non-matched cards turn face down on the next move (if not controlled by others)
 */
export class Board {
    rows;
    cols;
    grid; // null represents removed card
    players;
    waitingForCard; // position key -> waiting queue
    changeListeners; // listeners waiting for board changes
    // Abstraction function:
    //   AF(rows, cols, grid, players, waitingForCard, changeListeners) =
    //     A Memory Scramble game board with dimensions rows x cols,
    //     where grid[r][c] represents the card at position (r, c):
    //       - null means no card (it was removed after matching)
    //       - Card object with value, state ('down' or 'up'), and controller (player ID or undefined)
    //     players maps player IDs to Player objects tracking their controlled cards
    //     waitingForCard maps card positions to queues of players waiting to control that card
    //     changeListeners contains deferred promises waiting for the next board change
    //
    // Representation invariant:
    //   - rows > 0 and cols > 0
    //   - grid.length === rows
    //   - for all r in [0, rows): grid[r].length === cols
    //   - for all cards in grid: if card !== null, then:
    //       - card.value is non-empty and contains no whitespace/newlines
    //       - if card.controller !== undefined, then card.state === 'up'
    //       - if card.controller !== undefined, then players.has(card.controller)
    //   - for all player in players.values():
    //       - if player.firstCard is defined, grid[firstCard.row][firstCard.column] !== null
    //         and that card's controller === player.playerId
    //       - if player.secondCard is defined, then player.firstCard is also defined
    //       - if player.secondCard is defined, grid[secondCard.row][secondCard.column] !== null
    //         and that card's controller === player.playerId
    //   - waitingForCard keys are valid positions "row,col" where 0 <= row < rows and 0 <= col < cols
    //
    // Safety from rep exposure:
    //   - All fields are private and readonly (the collections themselves)
    //   - grid is mutable but never returned directly; methods return string representations
    //   - players, waitingForCard, changeListeners are private and never exposed
    //   - Card and Player objects are never returned directly to clients
    //   - The only public output is string representations of the board state via look()
    //   - Position objects are readonly interfaces, safe to share
    /**
     * Construct a new Board with the given dimensions and cards.
     *
     * @param rows number of rows, must be positive
     * @param cols number of columns, must be positive
     * @param cards array of card values in row-major order, length must equal rows * cols
     * @throws Error if dimensions or cards are invalid
     */
    constructor(rows, cols, cards) {
        if (rows <= 0 || cols <= 0) {
            throw new Error('Board dimensions must be positive');
        }
        if (cards.length !== rows * cols) {
            throw new Error(`Expected ${rows * cols} cards, got ${cards.length}`);
        }
        this.rows = rows;
        this.cols = cols;
        this.grid = [];
        this.players = new Map();
        this.waitingForCard = new Map();
        this.changeListeners = [];
        // Initialize grid with face-down cards
        for (let r = 0; r < rows; r++) {
            const row = [];
            for (let c = 0; c < cols; c++) {
                const value = cards[r * cols + c];
                if (!value) {
                    throw new Error('Card value cannot be undefined');
                }
                row.push(new Card(value, 'down', undefined));
            }
            this.grid.push(row);
        }
        this.checkRep();
    }
    /**
     * Check the representation invariant.
     * @throws Error if rep invariant is violated
     */
    checkRep() {
        assert(this.rows > 0, 'rows must be positive');
        assert(this.cols > 0, 'cols must be positive');
        assert(this.grid.length === this.rows, 'grid must have correct number of rows');
        for (let r = 0; r < this.rows; r++) {
            assert(this.grid[r].length === this.cols, `row ${r} must have correct number of columns`);
            for (let c = 0; c < this.cols; c++) {
                const card = this.grid[r][c];
                if (card !== null) {
                    // Card invariants are checked by Card constructor
                    if (card.isControlled()) {
                        assert(card.isFaceUp(), 'controlled card must be face up');
                        assert(this.players.has(card.controller), 'controller must be a registered player');
                    }
                }
            }
        }
        // Check player states
        for (const player of this.players.values()) {
            if (player.firstCard !== undefined) {
                const { row, column } = player.firstCard;
                const card = this.grid[row][column];
                assert(card !== null, 'first card must exist');
                assert(card.isControlledBy(player.playerId), 'first card must be controlled by player');
            }
            if (player.secondCard !== undefined) {
                assert(player.firstCard !== undefined, 'cannot have second card without first');
                const { row, column } = player.secondCard;
                const card = this.grid[row][column];
                assert(card !== null, 'second card must exist');
                assert(card.isControlledBy(player.playerId), 'second card must be controlled by player');
            }
        }
    }
    /**
     * Make a new board by parsing a file.
     *
     * File format:
     *   ROWSxCOLUMNS
     *   CARD1
     *   CARD2
     *   ...
     *
     * PS4 instructions: the specification of this method may not be changed.
     *
     * @param filename path to game board file
     * @returns a new board with the size and cards from the file
     * @throws Error if the file cannot be read or is not a valid game board
     */
    static async parseFromFile(filename) {
        const fileContents = await fs.promises.readFile(filename, 'utf-8');
        const lines = fileContents.split(/\r?\n/);
        if (lines.length < 2) {
            throw new Error('Invalid board file: too few lines');
        }
        // Parse dimensions from first line
        const dimensionMatch = lines[0].match(/^(\d+)x(\d+)$/);
        if (!dimensionMatch) {
            throw new Error('Invalid board file: first line must be ROWSxCOLUMNS');
        }
        const rows = parseInt(dimensionMatch[1]);
        const cols = parseInt(dimensionMatch[2]);
        // Parse cards from subsequent lines
        const cards = [];
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i];
            if (line && line.length > 0) { // Skip empty lines at end of file
                cards.push(line);
            }
        }
        if (cards.length !== rows * cols) {
            throw new Error(`Invalid board file: expected ${rows * cols} cards, got ${cards.length}`);
        }
        return new Board(rows, cols, cards);
    }
    /**
     * Get the board state from a player's perspective.
     *
     * Board state format:
     *   ROWSxCOLUMNS
     *   SPOT1
     *   SPOT2
     *   ...
     *
     * Where each SPOT is one of:
     *   - "none" for an empty space (removed card)
     *   - "down" for a face-down card
     *   - "up CARD" for a face-up card controlled by another player or no one
     *   - "my CARD" for a face-up card controlled by this player
     *
     * @param playerId ID of the player viewing the board
     * @returns string representation of the board state
     */
    look(playerId) {
        this.checkRep();
        this.ensurePlayerExists(playerId);
        let result = `${this.rows}x${this.cols}\n`;
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const card = this.grid[r][c];
                if (card === null) {
                    result += 'none\n';
                }
                else if (card.isFaceDown()) {
                    result += 'down\n';
                }
                else if (card.isControlledBy(playerId)) {
                    result += `my ${card.value}\n`;
                }
                else {
                    result += `up ${card.value}\n`;
                }
            }
        }
        this.checkRep();
        return result;
    }
    /**
     * Try to flip a card at the given position.
     * Implements all game rules including waiting for cards controlled by other players.
     *
     * Game rules:
     * 1. First card: player controls the card (waiting if another player controls it)
     * 2. Second card: if cards match, player keeps control; otherwise, relinquishes control
     * 3. Next move: matched cards are removed; non-matched cards turn face down (if not controlled)
     *
     * @param playerId ID of the player flipping the card
     * @param row row of the card (0-indexed from top)
     * @param column column of the card (0-indexed from left)
     * @throws Error if the flip operation fails (no card, controlled by another player for 2nd flip, etc.)
     */
    async flip(playerId, row, column) {
        this.checkRep();
        this.ensurePlayerExists(playerId);
        if (!this.isValidPosition(row, column)) {
            throw new Error('Invalid position');
        }
        const player = this.players.get(playerId);
        // Handle cleanup from previous turn (rules 3-A and 3-B)
        await this.handlePreviousTurnCleanup(player);
        const card = this.grid[row][column];
        // Rule 1-A and 2-A: no card at this position
        if (card === null) {
            this.checkRep();
            throw new Error('No card at this position');
        }
        if (!player.hasFirstCard()) {
            // Flipping first card
            await this.flipFirstCard(player, row, column, card);
        }
        else {
            // Flipping second card
            await this.flipSecondCard(player, row, column, card);
        }
        this.checkRep();
    }
    /**
     * Apply a transformation function to every card on the board.
     * Maintains pairwise consistency: matching cards are transformed together atomically.
     *
     * @param f transformation function from card value to new card value (must be mathematical function)
     */
    async map(f) {
        this.checkRep();
        // To maintain pairwise consistency, transform matching cards together
        // Build a map of unique card values to their positions
        const cardPositions = new Map();
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const card = this.grid[r][c];
                if (card !== null) {
                    if (!cardPositions.has(card.value)) {
                        cardPositions.set(card.value, []);
                    }
                    cardPositions.get(card.value).push({ row: r, column: c });
                }
            }
        }
        // Transform each unique card value once, then apply to all instances atomically
        for (const [oldValue, positions] of cardPositions.entries()) {
            const newValue = await f(oldValue);
            // Apply transformation to all instances of this card value
            for (const { row, column } of positions) {
                const card = this.grid[row][column];
                if (card !== null && card.value === oldValue) {
                    // Replace with new card preserving state and controller
                    this.grid[row][column] = card.withValue(newValue);
                }
            }
        }
        this.notifyChange();
        this.checkRep();
    }
    /**
     * Wait for the next change to the board.
     * A change is any card turning face up or down, being removed, or changing value.
     *
     * @returns promise that resolves when the board changes
     */
    async watchForChange() {
        const deferred = new Deferred();
        this.changeListeners.push(deferred);
        await deferred.promise;
    }
    // ========== Private Helper Methods ==========
    /**
     * Handle cleanup from the player's previous turn (rules 3-A and 3-B)
     */
    async handlePreviousTurnCleanup(player) {
        if (!player.hasFirstCard()) {
            return; // No previous turn to clean up
        }
        if (player.hasBothCards()) {
            // Rule 3-A: remove matching cards
            const card1 = this.grid[player.firstCard.row][player.firstCard.column];
            const card2 = this.grid[player.secondCard.row][player.secondCard.column];
            if (card1 !== null && card2 !== null && card1.matches(card2)) {
                this.grid[player.firstCard.row][player.firstCard.column] = null;
                this.grid[player.secondCard.row][player.secondCard.column] = null;
                this.notifyChange();
            }
        }
        else {
            // Rule 3-B: turn down non-matching card(s) if not controlled by others
            this.turnDownCardIfPossible(player.firstCard);
        }
        player.clearCards();
    }
    /**
     * Turn down a card if it's face up and not controlled by another player
     */
    turnDownCardIfPossible(position) {
        const card = this.grid[position.row][position.column];
        if (card !== null && card.isFaceUp() && !card.isControlled()) {
            this.grid[position.row][position.column] = card.withState('down');
            this.notifyChange();
        }
    }
    /**
     * Handle flipping the first card (rules 1-A through 1-D)
     */
    async flipFirstCard(player, row, column, card) {
        // Rule 1-D: wait if controlled by another player
        while (card.isControlled() && !card.isControlledBy(player.playerId)) {
            await this.waitForCard(row, column);
            // Re-check after waiting (card might have been removed)
            const cardNow = this.grid[row][column];
            if (cardNow === null) {
                throw new Error('No card at this position');
            }
        }
        // Rule 1-B: turn face up if down
        if (card.isFaceDown()) {
            this.grid[row][column] = card.withState('up');
            this.notifyChange();
            card = this.grid[row][column]; // Update reference
        }
        // Rule 1-C: take control
        this.grid[row][column] = card.withController(player.playerId);
        player.setFirstCard({ row, column });
    }
    /**
     * Handle flipping the second card (rules 2-A through 2-E)
     */
    async flipSecondCard(player, row, column, card) {
        // Rule 2-B: fail if controlled by any player (don't wait to avoid deadlock)
        if (card.isControlled()) {
            this.relinquishFirstCard(player);
            throw new Error('Card is controlled by another player');
        }
        // Rule 2-C: turn face up if down
        if (card.isFaceDown()) {
            this.grid[row][column] = card.withState('up');
            this.notifyChange();
            card = this.grid[row][column]; // Update reference
        }
        const firstCard = this.grid[player.firstCard.row][player.firstCard.column];
        // Rule 2-D and 2-E: check for match
        if (card.matches(firstCard)) {
            // Match! Keep control of both cards
            this.grid[row][column] = card.withController(player.playerId);
            player.setSecondCard({ row, column });
        }
        else {
            // No match, relinquish control of both cards
            this.relinquishFirstCard(player);
            // No need to set controller for current card as we never took control
        }
    }
    /**
     * Relinquish control of the player's first card
     */
    relinquishFirstCard(player) {
        if (player.firstCard !== undefined) {
            const { row, column } = player.firstCard;
            const card = this.grid[row][column];
            if (card !== null) {
                this.grid[row][column] = card.withController(undefined);
                this.notifyCardAvailable(row, column);
            }
            player.clearCards();
        }
    }
    /**
     * Ensure a player exists in the players map, creating if necessary.
     * @param playerId player ID
     * @throws Error if player ID is invalid
     */
    ensurePlayerExists(playerId) {
        if (!this.players.has(playerId)) {
            this.players.set(playerId, new Player(playerId));
        }
    }
    /**
     * Check if a position is valid on this board
     */
    isValidPosition(row, column) {
        return row >= 0 && row < this.rows && column >= 0 && column < this.cols;
    }
    /**
     * Wait for a card to become available (not controlled by another player).
     * @param row row of card
     * @param column column of card
     * @returns promise that resolves when the card is available
     */
    async waitForCard(row, column) {
        const key = this.positionKey(row, column);
        if (!this.waitingForCard.has(key)) {
            this.waitingForCard.set(key, []);
        }
        const deferred = new Deferred();
        this.waitingForCard.get(key).push(deferred);
        await deferred.promise;
    }
    /**
     * Notify waiting players that a card is now available.
     * @param row row of card
     * @param column column of card
     */
    notifyCardAvailable(row, column) {
        const key = this.positionKey(row, column);
        const waiting = this.waitingForCard.get(key);
        if (waiting && waiting.length > 0) {
            const deferred = waiting.shift();
            deferred.resolve();
        }
    }
    /**
     * Notify all change listeners that the board has changed.
     */
    notifyChange() {
        for (const deferred of this.changeListeners) {
            deferred.resolve();
        }
        this.changeListeners.length = 0; // Clear all listeners
    }
    /**
     * Create a string key for a position
     */
    positionKey(row, column) {
        return `${row},${column}`;
    }
    /**
     * String representation of the board (for debugging).
     * @returns string showing the board state
     */
    toString() {
        let result = `Board(${this.rows}x${this.cols}):\n`;
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const card = this.grid[r][c];
                if (card === null) {
                    result += '[none] ';
                }
                else {
                    result += `[${card.toString()}] `;
                }
            }
            result += '\n';
        }
        return result;
    }
}
//# sourceMappingURL=board.js.map