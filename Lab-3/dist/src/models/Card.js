/**
 * Card represents a single card in the Memory Scramble game.
 * Each card has a value (string), a state (face up or down),
 * and may be controlled by a player.
 *
 * This is an immutable data holder - modifications are done by the Board.
 */
export class Card {
    value;
    state;
    controller;
    /**
     * Construct a new Card
     *
     * @param value the card's value/label (non-empty, no whitespace)
     * @param state whether the card is face up or down
     * @param controller the player ID controlling this card, or undefined if not controlled
     */
    constructor(value, state, controller) {
        this.value = value;
        this.state = state;
        this.controller = controller;
        if (!value || /\s/.test(value)) {
            throw new Error('Card value must be non-empty and contain no whitespace');
        }
    }
    /**
     * Check if this card is controlled by any player
     */
    isControlled() {
        return this.controller !== undefined;
    }
    /**
     * Check if this card is controlled by a specific player
     */
    isControlledBy(playerId) {
        return this.controller === playerId;
    }
    /**
     * Check if this card is face down
     */
    isFaceDown() {
        return this.state === 'down';
    }
    /**
     * Check if this card is face up
     */
    isFaceUp() {
        return this.state === 'up';
    }
    /**
     * Check if this card matches another card
     */
    matches(other) {
        return this.value === other.value;
    }
    /**
     * Create a copy of this card with updated state
     */
    withState(newState) {
        return new Card(this.value, newState, this.controller);
    }
    /**
     * Create a copy of this card with updated controller
     */
    withController(newController) {
        return new Card(this.value, this.state, newController);
    }
    /**
     * Create a copy of this card with updated value
     */
    withValue(newValue) {
        return new Card(newValue, this.state, this.controller);
    }
    /**
     * String representation for debugging
     */
    toString() {
        const stateStr = this.state === 'down' ? 'D' : 'U';
        const ctrlStr = this.controller ? `(${this.controller})` : '';
        return `${this.value}${stateStr}${ctrlStr}`;
    }
}
//# sourceMappingURL=Card.js.map