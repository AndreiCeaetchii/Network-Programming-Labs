/**
 * Player represents a player in the Memory Scramble game.
 * Each player has a unique ID and tracks which cards they currently control.
 *
 * Representation invariant:
 *   - playerId is a non-empty string of alphanumeric or underscore characters
 *   - if secondCard is defined, then firstCard must also be defined
 */
export class Player {
    playerId;
    _firstCard;
    _secondCard;
    /**
     * Construct a new Player
     *
     * @param playerId unique identifier for this player, must match /^[a-zA-Z0-9_]+$/
     */
    constructor(playerId) {
        this.playerId = playerId;
        if (!/^[a-zA-Z0-9_]+$/.test(playerId)) {
            throw new Error('Player ID must be alphanumeric or underscore characters');
        }
        this._firstCard = undefined;
        this._secondCard = undefined;
        this.checkRep();
    }
    /**
     * Check representation invariant
     */
    checkRep() {
        if (this._secondCard !== undefined && this._firstCard === undefined) {
            throw new Error('Cannot have second card without first card');
        }
    }
    /**
     * Get the position of the first card controlled by this player
     */
    get firstCard() {
        return this._firstCard;
    }
    /**
     * Get the position of the second card controlled by this player
     */
    get secondCard() {
        return this._secondCard;
    }
    /**
     * Check if player has flipped their first card
     */
    hasFirstCard() {
        return this._firstCard !== undefined;
    }
    /**
     * Check if player has flipped both cards
     */
    hasBothCards() {
        return this._firstCard !== undefined && this._secondCard !== undefined;
    }
    /**
     * Set the first card controlled by this player
     */
    setFirstCard(position) {
        this._firstCard = position;
        this.checkRep();
    }
    /**
     * Set the second card controlled by this player
     */
    setSecondCard(position) {
        if (this._firstCard === undefined) {
            throw new Error('Cannot set second card without first card');
        }
        this._secondCard = position;
        this.checkRep();
    }
    /**
     * Check if the player's two cards match (have been checked to match)
     * This is determined by whether both cards are set
     */
    hasMatchingPair() {
        return this._firstCard !== undefined && this._secondCard !== undefined;
    }
    /**
     * Clear the cards controlled by this player
     */
    clearCards() {
        this._firstCard = undefined;
        this._secondCard = undefined;
        this.checkRep();
    }
    /**
     * String representation for debugging
     */
    toString() {
        return `Player(${this.playerId}, first=${this._firstCard ? `(${this._firstCard.row},${this._firstCard.column})` : 'none'}, second=${this._secondCard ? `(${this._secondCard.row},${this._secondCard.column})` : 'none'})`;
    }
}
//# sourceMappingURL=Player.js.map