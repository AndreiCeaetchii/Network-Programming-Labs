/* Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
 * Redistribution of original or derived work requires permission of course staff.
 */
import { Board } from './board.js';
/**
 * Example code for simulating a game.
 *
 * PS4 instructions: you may use, modify, or remove this file,
 *   completing it is recommended but not required.
 *
 * @throws Error if an error occurs reading or parsing the board
 */
async function simulationMain() {
    const filename = 'boards/ab.txt';
    const board = await Board.parseFromFile(filename);
    const size = 5;
    const players = 3; // Simulate 3 concurrent players
    const tries = 20;
    const maxDelayMilliseconds = 100;
    console.log('Starting simulation with', players, 'players,', tries, 'tries each');
    console.log('Initial board state:\n', board.toString());
    // start up one or more players as concurrent asynchronous function calls
    const playerPromises = [];
    for (let ii = 0; ii < players; ++ii) {
        playerPromises.push(player(ii));
    }
    // wait for all the players to finish (unless one throws an exception)
    await Promise.all(playerPromises);
    console.log('Simulation completed successfully!');
    console.log('Final board state:\n', board.toString());
    /** @param playerNumber player to simulate */
    async function player(playerNumber) {
        const playerId = `player${playerNumber}`;
        console.log(`${playerId} starting...`);
        for (let jj = 0; jj < tries; ++jj) {
            try {
                await timeout(Math.random() * maxDelayMilliseconds);
                // Try to flip over a first card at random position
                const row1 = randomInt(size);
                const col1 = randomInt(size);
                console.log(`${playerId} attempting first flip at (${row1},${col1})`);
                await board.flip(playerId, row1, col1);
                await timeout(Math.random() * maxDelayMilliseconds);
                // Try to flip over a second card at random position
                const row2 = randomInt(size);
                const col2 = randomInt(size);
                console.log(`${playerId} attempting second flip at (${row2},${col2})`);
                await board.flip(playerId, row2, col2);
            }
            catch (err) {
                if (err instanceof Error) {
                    console.log(`${playerId} flip failed: ${err.message}`);
                }
                else {
                    console.error(`${playerId} unexpected error:`, err);
                }
            }
        }
        console.log(`${playerId} finished`);
    }
}
/**
 * Random positive integer generator
 *
 * @param max a positive integer which is the upper bound of the generated number
 * @returns a random integer >= 0 and < max
 */
function randomInt(max) {
    return Math.floor(Math.random() * max);
}
/**
 * @param milliseconds duration to wait
 * @returns a promise that fulfills no less than `milliseconds` after timeout() was called
 */
async function timeout(milliseconds) {
    const { promise, resolve } = Promise.withResolvers();
    setTimeout(resolve, milliseconds);
    return promise;
}
void simulationMain();
//# sourceMappingURL=simulation.js.map