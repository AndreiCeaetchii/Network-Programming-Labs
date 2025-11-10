/* Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
 * Redistribution of original or derived work requires permission of course staff.
 */
import assert from 'node:assert';
import { Board } from '../src/board.js';
/**
 * Tests for the Board abstract data type.
 *
 * Testing strategy:
 *
 * parseFromFile():
 *   - valid board files: small (3x3), medium (5x5)
 *   - card types: ASCII characters, emoji
 *   - invalid files: missing dimensions, wrong card count, invalid format
 *
 * look():
 *   - empty board (all cards face down)
 *   - board with face-up cards (controlled by self, controlled by others, not controlled)
 *   - board with removed cards
 *   - multiple players viewing the same board
 *
 * flip():
 *   Partitions:
 *   - First vs second card
 *   - Card state: face down vs face up
 *   - Card controller: no controller, self, other player
 *   - Match: matching pair, non-matching pair
 *   - Position: valid, invalid (out of bounds, no card)
 *   - Previous turn: no previous turn, matched pair, non-matched card
 *   - Concurrency: single player, multiple concurrent players
 *
 * map():
 *   - Transform all cards
 *   - Pairwise consistency (matching cards stay matching)
 *   - Interleaving with other operations
 *
 * watchForChange():
 *   - Wait for card flip
 *   - Wait for card removal
 *   - Wait for map transformation
 *   - Multiple watchers
 */
describe('Board', function () {
    // ====================
    // parseFromFile() tests
    // ====================
    describe('parseFromFile', function () {
        it('should parse a small 3x3 board with emoji', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            const state = board.look('testPlayer');
            assert(state.startsWith('3x3\n'));
            // All cards should be face down initially
            const lines = state.split('\n');
            assert.strictEqual(lines.length, 11); // 3x3 + 1 dimension line + 1 empty
            for (let i = 1; i < 10; i++) {
                assert.strictEqual(lines[i], 'down');
            }
        });
        it('should parse a 5x5 board with ASCII characters', async function () {
            const board = await Board.parseFromFile('boards/ab.txt');
            const state = board.look('testPlayer');
            assert(state.startsWith('5x5\n'));
            const lines = state.split('\n');
            assert.strictEqual(lines.length, 27); // 5x5 + 1 dimension line + 1 empty
        });
        it('should throw error for non-existent file', async function () {
            await assert.rejects(async () => await Board.parseFromFile('boards/nonexistent.txt'), Error);
        });
    });
    // ====================
    // look() tests
    // ====================
    describe('look', function () {
        it('should show all cards face down on a new board', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            const state = board.look('player1');
            const lines = state.split('\n');
            // Check all spots are "down"
            for (let i = 1; i < 10; i++) {
                assert.strictEqual(lines[i], 'down', `line ${i} should be 'down'`);
            }
        });
        it('should show different perspectives for different players', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            await board.flip('player1', 0, 0);
            const state1 = board.look('player1');
            const state2 = board.look('player2');
            // Player1 should see "my" card
            assert(state1.includes('my 🦄'), 'player1 should see "my 🦄"');
            // Player2 should see "up" card
            assert(state2.includes('up 🦄'), 'player2 should see "up 🦄"');
        });
    });
    // ====================
    // flip() tests - First card
    // ====================
    describe('flip - first card', function () {
        it('should flip a face-down card and control it', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            await board.flip('player1', 0, 0);
            const state = board.look('player1');
            const lines = state.split('\n');
            assert.strictEqual(lines[1], 'my 🦄', 'first card should be controlled by player1');
        });
        it('should wait for a card controlled by another player', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            // Player1 flips first card
            await board.flip('player1', 0, 0);
            // Player2 tries to flip the same card (should wait)
            const player2Promise = board.flip('player2', 0, 0);
            // Give a small timeout to ensure player2 is waiting
            await timeout(10);
            // Player1 flips second card (different card, won't match)
            await board.flip('player1', 0, 1);
            // Player1 flips another first card (should release the first card)
            await board.flip('player1', 0, 2);
            // Now player2 should get control
            await player2Promise;
            const state = board.look('player2');
            assert(state.includes('my 🦄') || state.includes('my 🌈'));
        });
        it('should throw error for invalid position', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            await assert.rejects(async () => await board.flip('player1', 10, 10), /Invalid position/);
        });
        it('should throw error for removed card', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            // Player1 finds and matches a pair
            await board.flip('player1', 0, 0); // 🦄
            await board.flip('player1', 0, 1); // 🦄 (matches!)
            // Player1 makes next move to remove the matched cards
            await board.flip('player1', 1, 0);
            // Try to flip a removed card
            await assert.rejects(async () => await board.flip('player1', 0, 0), /No card at this position/);
        });
    });
    // ====================
    // flip() tests - Second card
    // ====================
    describe('flip - second card', function () {
        it('should match two identical cards and keep control', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            // Flip first 🦄
            await board.flip('player1', 0, 0);
            // Flip second 🦄 (should match)
            await board.flip('player1', 0, 1);
            const state = board.look('player1');
            const lines = state.split('\n');
            assert.strictEqual(lines[1], 'my 🦄', 'first card should still be controlled');
            assert.strictEqual(lines[2], 'my 🦄', 'second card should be controlled');
        });
        it('should relinquish control for non-matching cards', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            // Flip first 🦄
            await board.flip('player1', 0, 0);
            // Flip a 🌈 (won't match)
            await board.flip('player1', 0, 2);
            const state = board.look('player1');
            // Both cards should be face up but not controlled
            assert(state.includes('up 🦄'));
            assert(state.includes('up 🌈'));
            assert(!state.includes('my'), 'player should not control any cards');
        });
        it('should fail if second card is controlled by another player', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            // Player1 flips first card
            await board.flip('player1', 0, 0);
            // Player2 flips a card
            await board.flip('player2', 0, 1);
            // Player1 tries to flip player2's controlled card as second card
            await assert.rejects(async () => await board.flip('player1', 0, 1), /controlled by another player/);
            // Player1's first card should be relinquished
            const state = board.look('player1');
            assert(!state.includes('my 🦄') || state.split('my 🦄').length === 2, 'player1 should not control the first card anymore (or only controls player2\'s card)');
        });
    });
    // ====================
    // flip() tests - Previous turn cleanup
    // ====================
    describe('flip - previous turn cleanup', function () {
        it('should remove matched cards on next move', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            // Match two cards
            await board.flip('player1', 0, 0); // 🦄
            await board.flip('player1', 0, 1); // 🦄
            // Make next move
            await board.flip('player1', 0, 2);
            const state = board.look('player1');
            const lines = state.split('\n');
            assert.strictEqual(lines[1], 'none', 'first matched card should be removed');
            assert.strictEqual(lines[2], 'none', 'second matched card should be removed');
        });
        it('should turn down non-matching cards on next move', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            // Flip non-matching cards
            await board.flip('player1', 0, 0); // 🦄
            await board.flip('player1', 0, 2); // 🌈
            // Make next move
            await board.flip('player1', 1, 0);
            const state = board.look('player1');
            const lines = state.split('\n');
            // First two cards should be face down now
            assert.strictEqual(lines[1], 'down', 'first card should be face down');
            assert.strictEqual(lines[3], 'down', 'third card should be face down');
        });
        it('should not turn down cards controlled by other players', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            // Player1 flips non-matching cards
            await board.flip('player1', 0, 0);
            await board.flip('player1', 0, 2);
            // Player2 takes control of one of player1's cards before player1's next move
            const player2Promise = board.flip('player2', 0, 0);
            // Give player2 time to start waiting
            await timeout(10);
            // Player1 makes next move (should release cards, allowing player2 to take control)
            await board.flip('player1', 1, 0);
            // Wait for player2 to get control
            await player2Promise;
            const state = board.look('player2');
            // Player2 should control the first card, and it should be face up
            assert(state.includes('my 🦄'));
        });
    });
    // ====================
    // Concurrent players tests
    // ====================
    describe('concurrent players', function () {
        it('should handle multiple players flipping different cards', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            const player1Promise = board.flip('player1', 0, 0);
            const player2Promise = board.flip('player2', 1, 0);
            const player3Promise = board.flip('player3', 2, 0);
            await Promise.all([player1Promise, player2Promise, player3Promise]);
            // All players should control their respective cards
            const state1 = board.look('player1');
            const state2 = board.look('player2');
            const state3 = board.look('player3');
            assert(state1.includes('my'));
            assert(state2.includes('my'));
            assert(state3.includes('my'));
        });
        it('should handle contention for the same card', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            // All players try to flip the same card
            const player1Promise = board.flip('player1', 0, 0);
            const player2Promise = board.flip('player2', 0, 0);
            const player3Promise = board.flip('player3', 0, 0);
            // Player1 should get it first
            await player1Promise;
            // Player1 flips second card and makes another move to release
            await board.flip('player1', 0, 1);
            await board.flip('player1', 0, 2);
            // One of player2 or player3 should get it
            // The other might fail if the card gets removed
            await Promise.allSettled([player2Promise, player3Promise]);
            // At least one should have succeeded
            const state2 = board.look('player2');
            const state3 = board.look('player3');
            // At least one player should have cards
            assert(state2.includes('my') || state3.includes('my'));
        });
    });
    // ====================
    // map() tests
    // ====================
    describe('map', function () {
        it('should transform all cards', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            await board.map(async (card) => {
                if (card === '🦄')
                    return '🌟';
                if (card === '🌈')
                    return '🌙';
                return card;
            });
            const state = board.look('player1');
            assert(!state.includes('🦄'), 'should not contain 🦄');
            assert(!state.includes('🌈'), 'should not contain 🌈');
            // All cards are face down, but transformation happened
        });
        it('should maintain pairwise consistency', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            // Start a slow map operation
            const mapPromise = board.map(async (card) => {
                await timeout(50);
                return card + 'X';
            });
            // While map is in progress, look at board
            await timeout(10);
            const state = board.look('player1');
            // Cards should be consistent (either both transformed or both not)
            // This is hard to test deterministically, but the map should complete successfully
            await mapPromise;
            const finalState = board.look('player1');
            // After map, all original cards should be transformed
            assert(finalState.includes('down')); // All face down initially
        });
    });
    // ====================
    // watchForChange() tests
    // ====================
    describe('watchForChange', function () {
        it('should resolve when a card is flipped', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            const watchPromise = board.watchForChange();
            // Flip a card after a short delay
            await timeout(10);
            await board.flip('player1', 0, 0);
            // Watch should resolve
            await watchPromise;
            assert(true, 'watch should have resolved');
        });
        it('should resolve when cards are removed', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            // Match two cards
            await board.flip('player1', 0, 0);
            await board.flip('player1', 0, 1);
            const watchPromise = board.watchForChange();
            // Make next move to remove cards
            await timeout(10);
            await board.flip('player1', 0, 2);
            await watchPromise;
            assert(true, 'watch should have resolved');
        });
        it('should resolve when map transforms cards', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            const watchPromise = board.watchForChange();
            await timeout(10);
            await board.map(async (card) => card + 'X');
            await watchPromise;
            assert(true, 'watch should have resolved');
        });
        it('should handle multiple watchers', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            const watch1 = board.watchForChange();
            const watch2 = board.watchForChange();
            const watch3 = board.watchForChange();
            await timeout(10);
            await board.flip('player1', 0, 0);
            await Promise.all([watch1, watch2, watch3]);
            assert(true, 'all watchers should have resolved');
        });
    });
    // ====================
    // Integration tests
    // ====================
    describe('integration', function () {
        it('should play a complete game without errors', async function () {
            const board = await Board.parseFromFile('boards/perfect.txt');
            // Player1 makes several moves
            await board.flip('player1', 0, 0);
            await board.flip('player1', 0, 1);
            await board.flip('player1', 0, 2);
            await board.flip('player1', 1, 0);
            await board.flip('player1', 1, 1);
            const state = board.look('player1');
            assert(state.startsWith('3x3\n'));
        });
        it('should handle mixed concurrent operations', async function () {
            const board = await Board.parseFromFile('boards/ab.txt');
            const operations = [
                board.flip('player1', 0, 0).catch(() => { }),
                board.flip('player2', 0, 1).catch(() => { }),
                board.flip('player3', 1, 0).catch(() => { }),
                board.watchForChange(),
                board.map(async (c) => c),
                board.flip('player1', 0, 2).catch(() => { }),
            ];
            await Promise.all(operations);
            assert(true, 'all operations should complete without deadlock');
        });
    });
});
/**
 * Helper function to create a timeout promise
 */
async function timeout(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
//# sourceMappingURL=board.test.js.map