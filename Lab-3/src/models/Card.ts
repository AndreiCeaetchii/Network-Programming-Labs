/**
 * Represents the state of a card: face down or face up
 */
export type CardState = 'down' | 'up';

/**
 * Card represents a single card in the Memory Scramble game.
 * Each card has a value (string), a state (face up or down),
 * and may be controlled by a player.
 *
 * This is an immutable data holder - modifications are done by the Board.
 */
export class Card {
    /**
     * Construct a new Card
     *
     * @param value the card's value/label (non-empty, no whitespace)
     * @param state whether the card is face up or down
     * @param controller the player ID controlling this card, or undefined if not controlled
     */
    constructor(
        public value: string,
        public state: CardState,
        public controller: string | undefined
    ) {
        if (!value || /\s/.test(value)) {
            throw new Error('Card value must be non-empty and contain no whitespace');
        }
    }

    /**
     * Check if this card is controlled by any player
     */
    public isControlled(): boolean {
        return this.controller !== undefined;
    }

    /**
     * Check if this card is controlled by a specific player
     */
    public isControlledBy(playerId: string): boolean {
        return this.controller === playerId;
    }

    /**
     * Check if this card is face down
     */
    public isFaceDown(): boolean {
        return this.state === 'down';
    }

    /**
     * Check if this card is face up
     */
    public isFaceUp(): boolean {
        return this.state === 'up';
    }

    /**
     * Check if this card matches another card
     */
    public matches(other: Card): boolean {
        return this.value === other.value;
    }

    /**
     * Create a copy of this card with updated state
     */
    public withState(newState: CardState): Card {
        return new Card(this.value, newState, this.controller);
    }

    /**
     * Create a copy of this card with updated controller
     */
    public withController(newController: string | undefined): Card {
        return new Card(this.value, this.state, newController);
    }

    /**
     * Create a copy of this card with updated value
     */
    public withValue(newValue: string): Card {
        return new Card(newValue, this.state, this.controller);
    }

    /**
     * String representation for debugging
     */
    public toString(): string {
        const stateStr = this.state === 'down' ? 'D' : 'U';
        const ctrlStr = this.controller ? `(${this.controller})` : '';
        return `${this.value}${stateStr}${ctrlStr}`;
    }
}
